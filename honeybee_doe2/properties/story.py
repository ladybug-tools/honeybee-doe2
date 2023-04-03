# -*- coding: utf-8 -*-
# -*- Python Version: 2.7 -*
""" Doe2 'Story' Object."""
from honeybee.model import Model
from honeybee.room import Room
from honeybee.face import Face
from honeybee.facetype import face_types
from ladybug_geometry.geometry3d import Point3D
from ladybug_geometry.geometry2d import Polygon2D, Point2D
from ..geometry.polygon import DoePolygon
from ..utils.doe_formatters import short_name


class Doe2Story:
    def __init__(self, rooms, _story_no):
        self.rooms = rooms
        self.story_no = _story_no

    # TODO Model use doe2story object to get geometry of each story and stories rooms/zones
    @property
    def story_poly(self):
        return self._make_story_poly(self.rooms, self.story_no)

    @staticmethod
    def _make_story_poly(rooms, story_no):

        floor_geom = []

        for room in rooms:
            for face in room.faces:
                if str(face.type) == 'Floor':
                    floor_geom.append(face.geometry)

        if len(floor_geom) == 0:
            story_geom = floor_geom[0]
        else:
            # get the minimum z and use it for all the floors
            z = min(geo.plane.o.z for geo in floor_geom)
            # floors are horizontal - let's make them 2D polygons
            boundaries = [
                Polygon2D([Point2D(v.x, v.y) for v in floor.vertices])
                for floor in floor_geom
            ]

            # find the union of the boundary polygons
            boundaries = Polygon2D.boolean_union_all(boundaries, tolerance=0.1)

            # I don't know if this is the right assumption
            assert len(boundaries) == 1, \
                f'Story {story_no} generates more than one polygon ' \
                '[{len(boundaries)}]. Not in DOE2!'

            vertices = [Point3D(point.x, point.y, z) for point in boundaries[0].vertices]

            story_geom = Face.from_vertices(
                identifier="Level_{}".format(story_no),
                vertices=vertices)  # boundaries[0].vertices)
            story_geom.display_name = "Level_{}".format(story_no)

        stry_rm_geom = []

        for room in rooms:
            for face in room.faces:
                stry_rm_geom.append(face.properties.doe2.poly)
        nl = '\n'

        return story_geom.properties.doe2.poly + nl.join(
            str('\n' + f) for f in stry_rm_geom)

    @property
    def space_height(self):
        return self._make_space_height(self.rooms)

    @staticmethod
    def _make_space_height(objs):
        # TODO un-hardcode this
        return objs[0].average_floor_height

    @property
    def floor_to_floor_height(self):
        return self._make_floor_to_floor_height(self.rooms)

    @staticmethod
    def _make_floor_to_floor_height(rooms):
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

    def to_inp(self):
        room_objs = [f.properties.doe2.space for f in self.rooms]

        inp_obj = '\n"Level_{self.story_no}"= FLOOR'.format(self=self) + \
            "\n   SHAPE           = POLYGON" + \
            '\n   POLYGON         = "Level_{self.story_no} Plg"'.format(self=self) + \
            '\n   SPACE-HEIGHT    = {self.space_height}'.format(self=self) + \
            '\n   FLOOR-HEIGHT    = {self.floor_to_floor_height}'.format(self=self) + \
            '\n   ..\n'
        nl = '\n'

        return inp_obj + nl.join(str('\n'+f) for f in room_objs)

    def __repr__(self):
        return self.to_inp()
