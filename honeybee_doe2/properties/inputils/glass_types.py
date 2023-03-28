from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.material.glazing import EnergyWindowMaterialGlazing, \
    EnergyWindowMaterialSimpleGlazSys

from honeybee_energy.construction.window import WindowConstruction
from ...utils.doe_formatters import short_name, unit_convertor


class GlassType():
    """ Doe2 Glass type, (window construction)"""

    def __init__(self, name, shading_coef, glass_cond):
        self.name = name
        self.shading_coef = shading_coef
        self.glass_cond = glass_cond

    @classmethod
    def from_hb_window_constr(cls, hb_window_constr):

        simple_window_con = hb_window_constr.to_simple_construction()
        simple_window_mat = simple_window_con.materials[0]

        shading_coef = simple_window_mat.shgc / 0.87

        glass_cond = unit_convertor(
            [simple_window_mat.u_factor], 'Btu/h-ft2-F', 'W/m2-K')

        name = simple_window_con.identifier
        name = short_name(name, 32)

        return cls(name=name, shading_coef=shading_coef, glass_cond=glass_cond)

    def to_inp(self) -> str:
        return '"{}" = GLASS-TYPE\n'.format(short_name(self.name, 32)) + \
               '   TYPE               = SHADING-COEF\n' +\
               '   SHADING-COEF       = {}\n'.format(self.shading_coef) + \
               '   GLASS-CONDUCT      = {}\n   ..\n'.format(self.glass_cond)

    def __repr__(self):
        return self.to_inp()
