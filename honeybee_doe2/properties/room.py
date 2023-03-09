# -*- coding: utf-8 -*-
# -*- Python Version: 2.7 -*-

from honeybee.room import Room
from ..utils.doe_formatters import short_name

from honeybee.face import Face
from honeybee.facetype import face_types
from .wall import DoeWall


class RoomDoe2Properties(object):
    def __init__(self, _host):
        self._host = _host

    @property
    def host(self):
        return self._host

    def duplicate(self, new_host=None):

        _host = new_host or self._host
        new_properties_obj = RoomDoe2Properties(_host)
        return new_properties_obj

    @property
    def poly(self):
        # * return self's floor's face's poly
        return self._get_floor_poly(self.host)

    @staticmethod
    def _get_floor_poly(obj):

        for face in obj.faces:
            if isinstance(face, type(face_types.floor)):
                return face.properties.doe2.poly

    @property
    def walls(self):
        # * Needs to return list of DoeWall objects
        return self._get_walls(self.host)

    @staticmethod
    def _get_walls(obj):
        walls = []
        for face in obj.faces:
            if isinstance(face, type(face_types.wall)):
                walls.append(DoeWall(face))
        return walls

    @property
    def window(self):
        pass
    # TODO add window support

    @property
    def door(self):
        pass
    # TODO add door support

    @property
    def activity_disc(self):
        pass
    # TODO add activity disc // loads support etc

    @property
    def space(self):
        return self._make_doe_space_obj(self.host)

    @staticmethod
    def _make_doe_space_obj(obj):

        spaceobj = ''
        obj_lines = []
        obj_lines.append('"{}" = SPACE\n'.format(short_name(obj.display_name)))
        obj_lines.append('   SHAPE           = POLYGON\n')
        obj_lines.append('   POLYGON         = "{} Plg"\n'.format(
            short_name(obj.display_name)))
        #obj_lines.append('   C-ACTIVITY-DESC = *{}*\n   ..\n'.format(str(obj.properties.energy.program_type)))
        return spaceobj.join([l for l in obj_lines])
