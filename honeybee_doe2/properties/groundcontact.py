# -*- coding: utf-8 -*-
# -*- Python Version: 2.7 -*-
from ..utils.doe_formatters import short_name

# ? Sooo equest is odd, but this is the way with having the undrgnd wall
# *


class GroundFloor:
    def __init__(self, face):
        self.face = face

    def to_inp(self, space_origin):

        azimuth = 180 if self.face.azimuth == 0 else self.face.azimuth
        origin_pt = self.face.geometry.lower_left_corner - space_origin

        obj_lines = []
        obj_lines.append(
            '"{}" = UNDERGROUND-WALL'.format(short_name(self.face.display_name)))
        obj_lines.append('\n  CONSTRUCTION = "{}_c"'.format(
            short_name(self.face.properties.energy.construction.display_name)))
        obj_lines.append('\n  LOCATION     = BOTTOM')
        obj_lines.append('\n  POLYGON      = "{} Plg"'.format(self.face.display_name))
        obj_lines.append('\n  AZIMUTH      = {}'.format(azimuth))
        obj_lines.append('\n  X            = {}'.format(origin_pt.x))
        obj_lines.append('\n  Y            = {}'.format(origin_pt.y))
        obj_lines.append('\n  Z            = {}'.format(origin_pt.z))
        obj_lines.append('\n  ..\n')

        return ''.join(obj_lines)

    def __repr__(self):
        return f'DOE2 ground floor: {self.face.display_name}'
