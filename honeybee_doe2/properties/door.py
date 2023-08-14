# -*- coding: utf-8 -*-

import math

from ladybug_geometry.geometry3d.face import Vector3D, Plane
from ..utils.doe_formatters import short_name


class Door:
    def __init__(self, door, parent):
        self.door = door
        self.parent = parent

    def to_inp(self):
        """Return an inp door string for an door."""

        construction = short_name(
            self.door.properties.energy.construction.display_name, 32)

        parent_llc = self.parent.geometry.lower_left_corner
        rel_plane = self.parent.geometry.plane
        apt_llc = self.door.geometry.lower_left_corner
        apt_urc = self.door.geometry.upper_right_corner

        # horizontal faces
        # horizontal Face3D; use world XY
        angle_tolerance = 0.01
        if rel_plane.n.angle(Vector3D(0, 0, 1)) <= angle_tolerance or \
                rel_plane.n.angle(Vector3D(0, 0, -1)) <= angle_tolerance:
            proj_x = Vector3D(1, 0, 0)
        else:
            proj_y = Vector3D(0, 0, 1).project(rel_plane.n)
            proj_x = proj_y.rotate(rel_plane.n, math.pi / -2)

        ref_plane = Plane(rel_plane.n, parent_llc, proj_x)
        min_2d = ref_plane.xyz_to_xy(apt_llc)
        max_2d = ref_plane.xyz_to_xy(apt_urc)
        height = max_2d.y - min_2d.y
        width = max_2d.x - min_2d.x

        return \
            '"{}" = DOOR\n'.format(short_name(self.door.display_name)) + \
            "\n  X             = {}".format(min_2d.x) + \
            "\n  Y             = {}".format(min_2d.y) + \
            "\n  WIDTH         = {}".format(width, 3) + \
            "\n  HEIGHT        = {}".format(height, 3) + \
            '\n  CONSTRUCTION    = "Generic Door"\n  ..\n'

    def __repr__(self):
        return self.to_inp()
