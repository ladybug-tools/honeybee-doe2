# -*- coding: utf-8 -*-
# -*- Python Version: 2.7 -*-
from ..utils.doe_formatters import short_name


class GroundFloor:
    def __init__(self, face):
        self.face = face

    def to_inp(self):
        obj_lines = []
        obj_lines.append(
            '"{}" = UNDERGROUND-FLOOR'.format(short_name(self.face.display_name)))
        obj_lines.append('\n  CONSTRUCTION = "{}_c"'.format(
            short_name(self.face.properties.energy.construction.display_name)))
        obj_lines.append('\n  LOCATION     = BOTTOM')
        obj_lines.append('\n  ..\n')

        return ''.join(obj_lines)

    def __repr__(self):
        return self.to_inp()
