from ladybug_geometry.geometry3d.face import Face3D
from ..utils.doe_formatters import short_name
from ..geometry.polygon import DoePolygon

from .aperture import Window


class DoeWallObj:
    def __init__(self, face):
        self.face = face

    def to_inp(self):

        doe_windows = [Window(ap) for ap in self.face.apertures]

        p_name = short_name(self.face.display_name)
        wall_typology = 'EXTERIOR' if str(
            self.face.boundary_condition) == 'Outdoors' else 'INTERIOR'

        constr = self.face.properties.energy.construction.display_name
        tilt = 90 - self.face.altitude
        azimuth = self.face.azimuth
        origin_pt = self.face.geometry.lower_left_corner

        spc = ''
        obj_lines = []

        obj_lines.append('"{}" = {}-WALL'.format(p_name, wall_typology))
        obj_lines.append('\n  POLYGON           = "{}"'.format(p_name+' Plg'))
        obj_lines.append('\n  CONSTRUCTION      = "{}_c"'.format(short_name(constr, 30)))
        obj_lines.append('\n  TILT              =  {}'.format(tilt))
        obj_lines.append('\n  AZIMUTH           =  {}'.format(azimuth))
        obj_lines.append('\n  X                 =  {}'.format(origin_pt.x))
        obj_lines.append('\n  Y                 =  {}'.format(origin_pt.y))
        obj_lines.append('\n  Z                 =  {}'.format(origin_pt.z))
        obj_lines.append('\n  ..\n')

        temp_str = spc.join([line for line in obj_lines])

        nl = '\n'
        if doe_windows is not None:
            for window in doe_windows:
                temp_str += window.to_inp() + nl
            return temp_str
        else:
            return temp_str

    def __repr__(self):
        return self.to_inp()

# ? this feels like it should be somehow linked to honeybee.face_types if that makes sense?
# ? Like face.properties.doe2.face_obj


class DoeWall:
    def __init__(self, _face):
        self._face = _face

    @property
    def face(self):
        return self._face

    @property
    def wall_poly(self):
        return self._make_wall_poly(self.face.geometry.polygon2d)

    @staticmethod
    def _make_wall_poly(obj):
        return DoePolygon.from_vertices(
            short_name(obj.display_name),
            obj.geometry.lower_left_counter_clockwise_vertices)

    @property
    def wall_obj(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return self._create_wall_obj(self.face)

    @staticmethod
    def _create_wall_obj(obj):
        return DoeWallObj(obj)
