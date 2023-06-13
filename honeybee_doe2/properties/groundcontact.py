from ..utils.doe_formatters import short_name
from ..geometry.polygon import DoePolygon

# ? Sooo equest is odd, but this is the way with having the undrgnd wall
# *


class GroundFloor:
    def __init__(self, face):
        self.face = face
        self.polygon = DoePolygon.from_face(face, flip=True)

    def to_inp(self, space_origin):
        azimuth = 180
        origin_pt = self.face.geometry.lower_left_corner - space_origin

        # create a unique polygon for ground floor faces
        polygon_name = f'{self.face.display_name}_ug Plg'
        polygon = self.polygon.to_inp(name=polygon_name) + '\n'
        obj_lines = [polygon]
        obj_lines.append(
            '"{}" = UNDERGROUND-WALL'.format(short_name(self.face.display_name)))
        obj_lines.append('\n  CONSTRUCTION = "{}_c"'.format(
            short_name(self.face.properties.energy.construction.display_name)))
        obj_lines.append('\n  LOCATION     = BOTTOM')
        obj_lines.append('\n  POLYGON      = "{}"'.format(polygon_name))
        obj_lines.append('\n  AZIMUTH      = {}'.format(azimuth))
        obj_lines.append('\n  X            = {}'.format(origin_pt.x))
        obj_lines.append('\n  Y            = {}'.format(origin_pt.y))
        obj_lines.append('\n  Z            = {}'.format(origin_pt.z))
        obj_lines.append('\n  ..\n')

        return ''.join(obj_lines)

    def __repr__(self):
        return f'DOE2 ground floor: {self.face.display_name}'
