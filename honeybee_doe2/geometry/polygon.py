from ladybug_geometry.geometry3d.face import Face3D
from ..utils.doe_formatters import short_name
from honeybee.face import Face3D
# TODO this needs to be in properties not external I think, not important but move later


class DoePolygon(object):
    "A Doe2 Polygon."

    def __init__(self, name, vertices):
        self.name = name
        self.vertice = vertices

    @classmethod
    def from_face(cls, face):

        name = short_name(face.display_name)
        vertices = face.geometry.polygon2d.vertices

        return cls(name=name, vertices=vertices)

    @classmethod
    def from_vertices(cls, name, vertices):
        return cls(name=name, vertices=vertices)

    def to_inp(self):
        """Returns Room Polygons block input"""
        vertices_template = '   V%d\t\t= ( %f, %f )'.replace('\t', '    ')
        vertices = '\n'.join([
            vertices_template % (i + 1, ver.x, ver.y)
            for i, ver in enumerate(self.vertice)
        ])
        return f'"{self.name} Plg" = POLYGON\n' \
               f'{vertices}\n' + \
               '   ..'

    def __repr__(self):
        return self.to_inp()
