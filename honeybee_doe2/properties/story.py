# -*- coding: utf-8 -*-
# -*- Python Version: 2.7 -*
""" Doe2 'Story' Object."""
from honeybee.model import Model
from honeybee.room import Room
from honeybee.face import Face
from honeybee.facetype import face_types
from ladybug_geometry.geometry3d.polyface import Polyface3D
from ladybug_geometry.geometry3d.pointvector import Point3D

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

        floorgeom = []

        for room in rooms:
            for face in room.faces:
                if str(face.type) == 'Floor':
                    floorgeom.append(face.geometry)

        floor_geom = Polyface3D.from_faces(floorgeom, 0.01)
        seg_vertices = []
        for segment in floor_geom.naked_edges:
            seg_vertices.append(segment.vertices)

        vertices = []
        for seg in seg_vertices:
            for vert in seg:
                vertices.append(vert)

        story_geom = Face.from_vertices(
            identifier="Level_{}".format(story_no),
            vertices=vertices)
        story_geom.remove_colinear_vertices(0.01)

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
