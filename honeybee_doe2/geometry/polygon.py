from ladybug_geometry.geometry3d.face import Face3D
from ..utils.doe_formatters import short_name
from honeybee.face import Face3D
from ladybug_geometry.geometry3d import Vector3D, Point3D, Plane, Face3D
import math
# TODO this needs to be in properties not external I think, not important but move later


class DoePolygon(object):
    "A Doe2 Polygon."

    def __init__(self, name, vertices):
        self.name = name
        self.vertice = vertices

    @classmethod
    def from_face(cls, face):

        name = short_name(face.display_name)

        my_face3d = face.geometry

        rel_plane = my_face3d.plane
        if rel_plane.n.z == 1 or rel_plane.n.z == -1:  # horizontal Face3D; use world XY
            ref_plane = Plane(rel_plane.n, my_face3d.lower_left_corner,
                              Vector3D(1, 0, 0))
        else:  # vertical or tilted Face3D; orient the Y to the workld Z
            proj_y = Vector3D(0, 0, 1).project(rel_plane.n)
            proj_x = proj_y.rotate(rel_plane.n, math.pi / -2)
            ref_plane = Plane(rel_plane.n, my_face3d.lower_left_corner, proj_x)
        vertices = [ref_plane.xyz_to_xy(pt) for pt in my_face3d]
        #vertices = face.geometry.polygon2d.vertices

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
