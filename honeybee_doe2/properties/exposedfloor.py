from ..utils.doe_formatters import short_name
from ..geometry.polygon import DoePolygon


class ExposedFloor:
    def __init__(self, face):
        self.face = face
        # only flip horizontal floors
        flip = True if abs(self.face.altitude + 90) <= 0.01 \
            else False
        self.polygon = DoePolygon.from_face(face, flip=flip)

    def to_inp(self, space_origin):

        p_name = short_name(self.face.display_name)

        constr = self.face.properties.energy.construction.display_name
        tilt = 90 - self.face.altitude
        azimuth = 180 if abs(180 - tilt) <= 0.01 else self.face.azimuth
        origin_pt = self.face.geometry.lower_left_corner - space_origin

        # create a unique polygon for exposed floor faces
        polygon_name = f'{self.face.display_name}_ef Plg'
        polygon = self.polygon.to_inp(name=polygon_name) + '\n'
        obj_lines = [polygon]

        obj_lines.append('"{}" = EXTERIOR-WALL'.format(p_name))
        obj_lines.append('\n  CONSTRUCTION      = "{}_c"'.format(short_name(constr, 30)))
        obj_lines.append('\n  LOCATION          = BOTTOM')
        obj_lines.append('\n  POLYGON           = "{}"'.format(polygon_name))
        obj_lines.append('\n  TILT              =  {}'.format(tilt))
        obj_lines.append('\n  AZIMUTH           =  {}'.format(azimuth))
        obj_lines.append('\n  X                 =  {}'.format(origin_pt.x))
        obj_lines.append('\n  Y                 =  {}'.format(origin_pt.y))
        obj_lines.append('\n  Z                 =  {}'.format(origin_pt.z))
        obj_lines.append('\n  ..\n')

        return ''.join([line for line in obj_lines])

    def __repr__(self):
        return f'DOE2 Wall: {self.face.display_name}'
