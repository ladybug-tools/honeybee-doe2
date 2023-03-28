# -*- coding: utf-8 -*-
# -*- Python Version: 2.7 -*-
from ladybug_geometry.geometry3d.face import Face3D
from honeybee.face import Face
from honeybee.aperture import Aperture

from ..utils.doe_formatters import short_name
from ..utils.glass_types import GlassType


class Window:
    def __init__(self, _aperture):
        self.aperture = _aperture

    def to_inp(self):

        glass_type = short_name(
            self.aperture.properties.energy.construction.display_name, 32)

        geo = self.aperture.geometry
        normal = geo.normal
        min_ = geo.min
        max_ = geo.max
        center = (min_ + max_) / 2
        ref_plane = geo._upper_oriented_plane()
        min_2d = ref_plane.xyz_to_xy(min_)
        max_2d = ref_plane.xyz_to_xy(max_)
        height = max_2d.y - min_2d.y
        width = max_2d.x - min_2d.x

        return \
            "{} = WINDOW\n".format(self.name) + \
            "\n  X             = {}".format(origin.x) + \
            "\n  Y             = {}".format(origin.y) + \
            "\n  WIDTH         = {}".format(width) + \
            "\n  HEIGHT        = {}".format(height) + \
            "\n  GLASS-TYPE    = {}".format(glass_type) + "\n  ..\n"
