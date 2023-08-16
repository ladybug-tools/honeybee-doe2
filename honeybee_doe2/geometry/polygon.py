import math
from typing import List

from honeybee.face import Face
from ladybug_geometry.geometry3d import Vector3D, Plane, Face3D
from ladybug_geometry.geometry2d import Point2D, Polygon2D

from ..utils.doe_formatters import short_name


class DoePolygon(object):
    "A Doe2 Polygon."

    def __init__(self, name, vertices, flip=False):
        self.name = name
        self.vertices = self._remove_duplicate_vertices(vertices, 0.003)
        self.flip = flip

    @staticmethod
    def _remove_duplicate_vertices(vertices: List[Point2D], tol=0.003):
        """Remove identical vertices."""
        pl = Polygon2D(vertices)
        pl = pl.remove_colinear_vertices(tol)
        return pl.vertices

    @classmethod
    def from_face(cls, face: Face, flip=False):
        """
        Create a DoePolygon from a Honeybee Face.

        Args:
            face: A Face object.

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

            if not flip and \
                    rel_plane.n.angle(Vector3D(0, 0, -1)) <= angle_tolerance:
                # change the order of the vertices. DOE2 expects the vertices to be
                # CCW from the top view
                vertices = [vertices[0]] + list(reversed(vertices[1:]))

        else:  # vertical or tilted Face3D; orient the Y to the world Z
            proj_y = Vector3D(0, 0, 1).project(rel_plane.n)
            proj_x = proj_y.rotate(rel_plane.n, math.pi / -2)
            ref_plane = Plane(rel_plane.n, geometry.lower_left_corner, proj_x)
            vertices = [
                Point2D(*ref_plane.xyz_to_xy(pt))
                for pt in geometry.lower_left_counter_clockwise_vertices]

        return cls(name=name, vertices=vertices, flip=flip)

    def to_inp(self, name=None):
        """Returns Polygons block input."""
        vertices_template = '   V%d\t\t= ( %f, %f )'.replace('\t', '    ')
        vertices = self.vertices
        if self.flip:
            # underground surface should be flipped
            vertices = [Point2D(v.x, -v.y) for v in vertices]
        vertices = '\n'.join([
            vertices_template % (i + 1, ver.x, ver.y)
            for i, ver in enumerate(vertices)
        ])
        name = name or f'{self.name} Plg'
        return f'"{name}" = POLYGON\n' \
               f'{vertices}\n' + \
               '   ..'

    def __repr__(self):
        return self.to_inp()
