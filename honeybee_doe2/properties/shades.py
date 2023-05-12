from dataclasses import dataclass
from typing import List
from honeybee.model import Model
from honeybee.shade import Shade
from ladybug_geometry.geometry3d.face import Face3D

from ..utils.doe_formatters import short_name
from ..geometry.polygon import DoePolygon


@dataclass
class Doe2Shade:
    name: str
    shade_type: str
    tilt: float
    azimuth: float
    x: float
    y: float
    z: float
    polygon: DoePolygon
    transmittance: float = 0.0

    """ DOE2 shade object. Can be either:
    -  'FIXED-SHADE': azimuth is independent from the building, i.e context shade such as
        buildings and terrain. Objects that are independent from the orientation of the
        building during ASHRAE 90.1 baseline orientation averages.
    -  'BUILDING-SHADE': azimuth is connected to the buildign azimuth,
          will rotate withh the building on change of azimuth, i.e fin shades, awnings, and
          other types of "on building" shading devices.

    """
    @classmethod
    def from_hb_shade(cls, shade: Shade):

        origin = shade.geometry.lower_left_corner
        face = shade.geometry
        face = face if face.normal.z <= 0 else face.flip()

        polygon = DoePolygon.from_face(face, flip=False)

        name = short_name(shade.display_name)
        shade_type = "FIXED-SHADE"  # TODO: Evaluate if this is the right default
        tilt = 90 - face.altitude
        azimuth = face.azimuth
        x = origin.x
        y = origin.y
        z = origin.z

        return cls(
            name=name, shade_type=shade_type, tilt=tilt, azimuth=azimuth, x=x, y=y, z=z,
            polygon=polygon)

    def to_inp(self):
        """Returns *.inp shade object string"""

        polygon_name = f'{self.name}_Plg'
        polygon = self.polygon.to_inp(name=polygon_name) + '\n'
        obj_lines = [polygon]

        obj_lines.append(f'"{self.name}" = {self.shade_type}')
        obj_lines.append(f'\n  TRANSMITTANCE    = {self.transmittance}')
        obj_lines.append(f'\n  SHAPE            = POLYGON')
        obj_lines.append(f'\n  POLYGON          = "{polygon_name}"')
        obj_lines.append(f'\n  TILT             = {self.tilt}')
        obj_lines.append(f'\n  AZIMUTH          = {self.azimuth}')
        obj_lines.append(f'\n  X                = {self.x}')
        obj_lines.append(f'\n  Y                = {self.y}')
        obj_lines.append(f'\n  Z                = {self.z}')
        obj_lines.append(f'\n  ..')

        return ''.join([line for line in obj_lines])

    def __repr__(self):
        return self.to_inp()


@dataclass
class Doe2ShadeCollection:

    doe_shades: List[Doe2Shade]

    @classmethod
    def from_df_context_shades(cls, df_shades: [ContextShade]):
        """Generate doe2 fixed shades from dragonfly context shades"""
        shade_faces = []

        for shade_i, shade in enumerate(df_shades):
            for i, geom in enumerate(shade.geometry):
                shade_geom_name = f"shade_{shade_i}_geom{i}"
                shade_faces.append((geom, shade_geom_name))
        doe_shades = [Doe2Shade.from_face3d(obj[0], obj[1]) for obj in shade_faces]

        return cls(doe_shades=doe_shades)

    def to_inp(self):

        block = [fb.fix_bldg_shade]
        shades = [shade.to_inp() for shade in self.doe_shades]

        block.append('\n\n'.join(shades))

        return '\n'.join(block)

    def __repr__(self):
        return self.to_inp()
