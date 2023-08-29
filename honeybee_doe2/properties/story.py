# -*- coding: utf-8 -*-
# -*- Python Version: 2.7 -*
""" Doe2 'Story' Object."""
from typing import List
from honeybee.room import Room
from honeybee.face import Face


class Doe2Story:
    """This class represents a DOE2 FLOOR object."""

    def __init__(self, rooms: List[Room], story_number: int, tolerance: float):
        self.rooms = rooms
        self.story_no = story_number
        self.tolerance = tolerance
        self.story_poly, self.boundary_geometry = self._story_poly

    @property
    def _story_poly(self):
        tol = self.tolerance

        boundaries = Room.grouped_horizontal_boundary(
            self.rooms, tolerance=tol, floors_only=True
        )
        if not boundaries:
            # try to create the boundary with the whole volume. This is an edge case
            # that can happen in a few instances including when all the floor are air
            # boundaries
            boundaries = Room.grouped_horizontal_boundary(
                self.rooms, tolerance=tol, floors_only=False
            )

        if not boundaries:
            raise ValueError(
                f'Failed to create the floor for floor {self.story_no} that includes '
                f'{self.rooms[0]} and {self.rooms[1]}'
            )
        # pick the first boundary to represent the story
        vertices = boundaries[0] \
            .remove_colinear_vertices(tol) \
            .remove_duplicate_vertices(tol).boundary  # use boundary to ignore holes if any

        story_geom = Face.from_vertices(
            identifier="Level_{}".format(self.story_no),
            vertices=vertices)
        story_geom.display_name = "Level_{}".format(self.story_no)

        story_rm_geom = []

        story_rm_geom.append(story_geom.properties.doe2.poly)

        for room in self.rooms:
            story_rm_geom.append(room.properties.doe2.poly(tol))
            for face in room.faces:
                story_rm_geom.append(face.properties.doe2.poly)
        story_rm_geom = '\n'.join(story_rm_geom)

        return '\n'.join([story_rm_geom]), story_geom

    @property
    def space_height(self):
        # TODO un-hardcode this
        return self.rooms[0].average_floor_height

    @property
    def floor_to_floor_height(self):
        rooms = self.rooms
        ceil_heights = 0
        ceil_areas = 0
        for room in rooms:
            for face in room.faces:
                if str(face.type) == 'RoofCeiling':
                    ceil_heights += face.center.z * face.area
                    ceil_areas += face.area

        ceil_h = ceil_heights / ceil_areas
        ceil_l = rooms[0].average_floor_height
        return ceil_h - ceil_l

    @property
    def display_name(self):
        return "Level_{}".format(self.story_no)

    def to_inp(self):
        origin_pt = self.boundary_geometry.geometry.lower_left_corner
        azimuth = self.boundary_geometry.azimuth
        room_objs = [f.properties.doe2.space(origin_pt) for f in self.rooms]

        inp_obj = '\n"{self.display_name}"= FLOOR'.format(self=self) + \
            "\n   SHAPE           = POLYGON" + \
            '\n   POLYGON         = "Level_{self.story_no} Plg"'.format(self=self) + \
            '\n   AZIMUTH         = {}'.format(azimuth) + \
            '\n   X               = {}'.format(origin_pt.x) + \
            '\n   Y               = {}'.format(origin_pt.y) + \
            '\n   Z               = {}'.format(origin_pt.z) + \
            '\n   SPACE-HEIGHT    = {self.floor_to_floor_height}'.format(self=self) + \
            '\n   FLOOR-HEIGHT    = {self.floor_to_floor_height}'.format(self=self) + \
            '\n   ..\n'
        nl = '\n'

        return inp_obj + nl.join(str('\n'+f) for f in room_objs)

    def __repr__(self):
        return self.to_inp()
