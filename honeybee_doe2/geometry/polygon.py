from ..utils.doe_formatters import short_name
from honeybee.face import Face
from ladybug_geometry.geometry3d import Vector3D, Plane, Face3D
from ladybug_geometry.geometry2d import Point2D
import math

from honeybee.facetype import RoofCeiling


class DoePolygon(object):
    "A Doe2 Polygon."

    def __init__(self, name, vertices):
        self.name = name
        self.vertices = vertices

    @classmethod
    def from_face(cls, face: Face):
        """
        Create a DoePolygon from a Honeybee Face.

        Args:
            face: A Face3D object.

        """
        name = short_name(face.display_name)

        geometry: Face3D = face.geometry

        rel_plane = geometry.plane
        # horizontal Face3D; use world XY
        angle_tolerance = 0.01
        if rel_plane.n.angle(Vector3D(0, 0, 1)) <= angle_tolerance or \
                rel_plane.n.angle(Vector3D(0, 0, -1)) <= angle_tolerance:
            llc_3d = geometry.lower_left_corner
            llc = Point2D(llc_3d.x, llc_3d.y)
            vertices = [
                Point2D(v[0] - llc.x, v[1] - llc.y) for v in
                geometry.lower_left_counter_clockwise_vertices
            ]
            #vertices = geometry.lower_left_counter_clockwise_vertices
        else:  # vertical or tilted Face3D; orient the Y to the world Z
            proj_y = Vector3D(0, 0, 1).project(rel_plane.n)
            proj_x = proj_y.rotate(rel_plane.n, math.pi / -2)
            ref_plane = Plane(rel_plane.n, geometry.lower_left_corner, proj_x)
            vertices = [
                Point2D(*ref_plane.xyz_to_xy(pt))
                for pt in geometry.lower_left_counter_clockwise_vertices]

        return cls(name=name, vertices=vertices)

    def to_inp(self):
        """Returns Polygons block input."""
        vertices_template = '   V%d\t\t= ( %f, %f )'.replace('\t', '    ')
        vertices = '\n'.join([
            vertices_template % (i + 1, ver.x, ver.y)
            for i, ver in enumerate(self.vertices)
        ])
        return f'"{self.name} Plg" = POLYGON\n' \
               f'{vertices}\n' + \
               '   ..'

    def __repr__(self):
        return self.to_inp()
