from ladybug_geometry.geometry3d.face import Face3D
from ..utils.doe_formatters import short_name


class DoeRoof:
    def __init__(self, face):
        self.face = face

    def to_inp(self, space_origin):

        p_name = short_name(self.face.display_name)

        constr = self.face.properties.energy.construction.display_name
        tilt = 90 - self.face.altitude
        azimuth = 180 if self.face.azimuth == 0 and tilt == 0 else self.face.azimuth
        origin_pt = self.face.geometry.lower_left_corner - space_origin

        return \
            '"{}" = ROOF'.format(p_name) + \
            '\n  POLYGON           = "{}"'.format(p_name+' Plg') + \
            '\n  CONSTRUCTION      = "{}_c"'.format(short_name(constr, 30)) + \
            '\n  TILT              =  {}'.format(tilt) + \
            '\n  AZIMUTH           =  {}'.format(azimuth) + \
            '\n  X                 =  {}'.format(origin_pt.x) + \
            '\n  Y                 =  {}'.format(origin_pt.y) + \
            '\n  Z                 =  {}'.format(origin_pt.z) + '\n  ..\n'


def __repr__(self):
    return f'DOE2 roof: {self.face.display_name}'
