from ladybug_geometry.geometry3d.face import Face3D
from ..utils.doe_formatters import short_name
from ..geometry.polygon import DoePolygon


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
        p_name = short_name(obj.display_name)
        constr = obj.properties.energy.construction.display_name
        # tilt
        # TODO Continue
