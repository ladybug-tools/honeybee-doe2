from ladybug_geometry.geometry3d.face import Face3D
from ..utils.doe_formatters import short_name
from ..geometry.polygon import DoePolygon


class DoeWallObj:
    def __init__(self, face):
        self._face = face

    def to_inp(self, face):

        p_name = short_name(face.display_name)
        wall_typology = 'EXTERIOR' if str(
            face.boundary_condition) == 'Outdoors' else 'INTERIOR'

        constr = face.properties.energy.construction.display_name
        tilt = 90.0  # TODO Un-hardcode wall tilt
        azimuth = face.azimuth
        origin_pt = face.geometry.lower_left_counter_clockwise_vertices[0]

        # TODO lookup wall trype for ext or int wall

        return \
            '"{}" = {}-WALL'.format(p_name, wall_typology) + \
            '\n  POLYGON           = "{}"'.format(p_name+' Plg') + \
            '\n  CONSTRUCTION      = "{}"'.format(constr) + \
            '\n  TILT              =  {}'.format(tilt) + \
            '\n  AZIMUTH           =  {}'.format(azimuth) + \
            '\n  X                 =  {}'.format(origin_pt.x) + \
            '\n  Y                 =  {}'.format(origin_pt.y) + \
            '\n  Z                 =  {}'.format(origin_pt.z) + '\n..\n'

    def __repr__(self):
        return self.to_inp(self._face)

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
        return self._make_wall_poly(self.face)

    @staticmethod  # M, this one?
    def _make_wall_poly(obj):
        # * 2d geometry
        return DoePolygon.from_vertices(
            short_name(obj.display_name), obj.geometry.polygon2d.vertices)

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
