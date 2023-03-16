# -*- coding: utf-8 -*-
# -*- Python Version: 2.7 -*-

from honeybee.room import Room
from ..utils.doe_formatters import short_name

from honeybee.face import Face
from honeybee.facetype import face_types
from .wall import DoeWallObj, DoeWall


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

        floor_face = [face for face in obj.faces if str(face.type) == 'Floor'][0]
        return floor_face.properties.doe2.poly

    @property
    def walls(self):
        # * Needs to return list of DoeWall objects
        return self._get_walls(self.host)

    @staticmethod
    def _get_walls(obj):
        walls = []
        for face in obj.faces:
            if str(face.type) == 'Wall':
                walls.append(DoeWallObj(face))
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
        return self._make_doe_space_obj(self.host, self.walls)

    @staticmethod
    def _make_doe_space_obj(obj, walls):

        floor_face = [face for face in obj.faces if str(face.type) == 'Floor'][0]
        #! Will break with multiple floor polygons

        spaceobj = ''
        obj_lines = []
        obj_lines.append('"{}" = SPACE\n'.format(short_name(obj.display_name)))
        obj_lines.append('   SHAPE           = POLYGON\n')
        obj_lines.append('   POLYGON         = "{} Plg"\n'.format(
            short_name(floor_face.display_name)))
        obj_lines.append('  VOLUME           = {}'.format(obj.volume))
        obj_lines.append('  ..\n')
        # obj_lines.append('   C-ACTIVITY-DESC = *{}*\n   ..\n'.format(str(obj.properties.energy.program_type)))
        temp_str = spaceobj.join([l for l in obj_lines])
        nl = '\n'

        return temp_str + nl.join('\n'+str(w) for w in walls)
