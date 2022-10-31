from honeybee_energy.construction.window import WindowConstruction
from honebee_energy.material.glazing import EnergyWindowMaterialGlazing, \
    EnergyWindowMaterialSimpleGlazSys

from honeybee_energy.construction.window import WindowConstruction
from ...utils.doe_formatters import short_name, unit_convertor


class GlassType():
    """ Doe2 Glass type, (window construction)"""

    def __inti__(self):
        self.name = None
        self.shading_coef = None
        self.glass_cond: None
