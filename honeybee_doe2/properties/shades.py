from dataclasses import dataclass
from typing import List
from math import degrees, isclose
import math

from honeybee.model import Model
from honeybee.shade import Shade
from ladybug_geometry.geometry3d.face import Face3D
from ladybug_geometry.geometry3d.pointvector import Vector3D
from ladybug_geometry.geometry3d.line import LineSegment3D
from ..utils.doe_formatters import short_name
from ..geometry.polygon import DoePolygon
from .inputils import blocks as fb


@dataclass
class Doe2Shade:
    # TODO: will need to change things up to support rm2d.shade_params
    """ DOE2 shade object. Can be either:
    -  'FIXED-SHADE': azimuth is independent from the building, i.e context shade such as
        buildings and terrain. Objects that are independent from the orientation of the 
        building during ASHRAE 90.1 baseline orientation averages. 
    -  'BUILDING-SHADE': azimuth is connected to the buildign azimuth,
          will rotate withh the building on change of azimuth, i.e fin shades, awnings, and
          other types of "on building" shading devices.

    """
    name: str
    shade_type: str
    x_ref: float
    y_ref: float
    z_ref: float
    azimuth: float
    tilt: float
    polygon: DoePolygon
    transmittance: float = 0.0

    @classmethod
    def from_shade(cls, shade: Shade):
        """Generate doe2 fixed shades  shades"""
        name = short_name(shade.display_name)
        shade_type = 'FIXED-SHADE'
        tolerance = 0.001
        if abs(shade.altitude + 90) <= tolerance:
            # horizontal facing down - flip the face so we can deal with them like
            # upwards facing shades. It doesn't make a difference in the results
            geometry = shade.geometry.flip()
            shade = Shade(name, geometry=geometry, is_detached=shade.is_detached)

        llc = shade.geometry.lower_left_corner
        tilt = 90 - shade.altitude
        azimuth = shade.azimuth
        if abs(tilt) <= tolerance:
            # set the azimuth to 180 for all the horizontal shade faces
            azimuth = 180

        x_ref = llc.x
        y_ref = llc.y
        z_ref = llc.z

        polygon = DoePolygon.from_face(shade)

        return cls(
            name=name, shade_type=shade_type, x_ref=x_ref, y_ref=y_ref, z_ref=z_ref,
            azimuth=azimuth, tilt=tilt, polygon=polygon, transmittance=0.0)

    def to_inp(self):
        """Returns *.inp shade object string"""
        obj_lines = [self.polygon.to_inp(), '\n\n']

        obj_lines.append(f'"{self.name}"       = {self.shade_type}\n')
        obj_lines.append('    SHAPE            = POLYGON\n')
        obj_lines.append(f'   POLYGON          = "{self.name} Plg"\n')
        obj_lines.append(f'   TRANSMITTANCE    = {self.transmittance}\n')
        obj_lines.append(f'   X-REF            = {self.x_ref}\n')
        obj_lines.append(f'   Y-REF            = {self.y_ref}\n')
        obj_lines.append(f'   Z-REF            = {self.z_ref}\n')
        obj_lines.append(f'   TILT             = {self.tilt}\n')
        obj_lines.append(f'   AZIMUTH          = {self.azimuth}\n   ..\n')

        return ''.join(obj_lines)

    def __repr__(self):
        return self.to_inp()


@dataclass
class Doe2ShadeCollection:

    doe_shades: List[Doe2Shade]

    @classmethod
    def from_hb_shades(cls, hb_shades: [Shade]):
        """Generate doe2 fixed shades  shades"""

        doe_shades = [Doe2Shade.from_shade(shade=shade)
                      for shade in hb_shades]

        return cls(doe_shades=doe_shades)

    def to_inp(self):

        block = [fb.fix_bldg_shade]
        shades = [shade.to_inp() for shade in self.doe_shades]

        block.append('\n\n'.join(shades))

        return '\n'.join(block)

    def __repr__(self):
        return self.to_inp()
