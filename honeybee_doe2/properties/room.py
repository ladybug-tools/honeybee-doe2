# -*- coding: utf-8 -*-
# -*- Python Version: 2.7 -*-

from honeybee.room import Room


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
    def space(self):
        return self._make_doe_space_obj(self.host)

    @staticmethod
    def _make_doe_space_obj(obj):
        spaceobj = ''
        obj_lines = []
        obj_lines.append('"{}" = SPACE\n'.format(obj.display_name))
        obj_lines.append('   SHAPE           = POLYGON\n')
        obj_lines.append('   POLYGON         = "{} Plg"\n'.format(obj.display_name))
        obj_lines.append(
            '   C-ACTIVITY-DESC = *{}*\n   ..\n'.format(str(obj.properties.energy.program_type)))
        return spaceobj.join([l for l in obj_lines])

    @property
    def poly(self):
        # * return self's floor's face's poly
        pass
    # TODO add space floor poly return

    @property
    def window(self):
        pass
    # TODO add window support

    @property
    def door(self):
        pass
    # TODO add door support
