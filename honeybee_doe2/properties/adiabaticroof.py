from ..utils.doe_formatters import short_name
from ..geometry.polygon import DoePolygon
from ladybug_geometry.geometry3d.face import Face3D


class AdiabaticRoof:
    def __init__(self, face):
        self.face = face

    def to_inp(self, space_origin):

        polygon = DoePolygon.from_face(self.face, flip=False)

        p_name = f'{short_name(self.face.display_name)}_ad'

        constr = self.face.properties.energy.construction.display_name
        tilt = 90 - self.face.altitude
        azimuth = 180 if abs(tilt) <= 0.01 else self.face.azimuth
        origin_pt = self.face.geometry.lower_left_corner - space_origin

        spc = ''

        obj_lines = [polygon.to_inp(p_name+' Plg')+'\n']

        obj_lines.append('"{}" = INTERIOR-WALL'.format(p_name))
        obj_lines.append('\n  POLYGON           = "{}"'.format(p_name+' Plg'))
        obj_lines.append('\n  CONSTRUCTION      = "{}_c"'.format(short_name(constr, 30)))
        obj_lines.append(
            '\n  NEXT-TO           =  "{}"'.format(self.face.parent.display_name))
        obj_lines.append('\n  INT-WALL-TYPE = ADIABATIC')
        obj_lines.append('\n  TILT              =  {}'.format(tilt))
        obj_lines.append('\n  AZIMUTH           =  {}'.format(azimuth))
        obj_lines.append('\n  X                 =  {}'.format(origin_pt.x))
        obj_lines.append('\n  Y                 =  {}'.format(origin_pt.y))
        obj_lines.append('\n  Z                 =  {}'.format(origin_pt.z))
        obj_lines.append('\n  ..\n')
        temp_str = spc.join([line for line in obj_lines])

        doe_windows = [
            Window(ap, self.face) for ap in self.face.apertures
        ]

        nl = '\n'
        if doe_windows is not None:
            for window in doe_windows:
                temp_str += window.to_inp() + nl
            return temp_str
        else:
            return temp_str


def __repr__(self):
    return f'DOE2 roof: {self.face.display_name}'
