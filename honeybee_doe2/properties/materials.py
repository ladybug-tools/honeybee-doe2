from enum import Enum
from honeybee_energy.material.opaque import EnergyMaterial, EnergyMaterialNoMass


from ..utils.doe_formatters import short_name, unit_convertor


class MaterialType(Enum):
    """Doe2 material types."""
    mass = 'PROPERTIES'
    no_mass = 'RESISTANCE'


class NoMassMaterial:
    def __init__(self, _name, _resistence):
        self._name = _name
        self._resistence = _resistence

    @property
    def name(self):
        return self._name

    @property
    def resistence(self):
        return self._resistence

    @classmethod
    def from_hb_material(cls, material):
        """Create a NoMassMaterial from a honeybee energy material no-mass."""

        assert isinstance(material, EnergyMaterialNoMass), \
            'Expected EnergyMaterialNoMass. Got {}.'.format(type(material))

        return cls(short_name(material.display_name, 32),
                   unit_convertor([material.r_value],
                                  'h-ft2-F/Btu', 'm2-K/W'))

    def to_inp(self):
        spc = ''
        obj_lines = []
        obj_lines.append('\n"{self._name}" = MATERIAL'.format(self=self))
        obj_lines.append(
            '\n   TYPE            = {}'.format(MaterialType.no_mass.value))
        obj_lines.append('\n  ..\n')

        return spc.join([l for l in obj_lines])

    def __repr__(self):
        return self.to_inp()


class MassMaterial:
    def __init__(self, _name, _thickness, _conductivity, _density, _specific_heat):
        self._name = _name
        self._thickness = _thickness
        self._conductivity = _conductivity
        self._density = _density
        self._specific_heat = _specific_heat

    @property
    def name(self):
        return self._name

    @property
    def thickness(self):
        return self._thickness

    @property
    def conductivity(self):
        return self._conductivity

    @property
    def density(self):
        return self._density

    @property
    def specific_heat(self):
        return self._specific_heat

    @classmethod
    def from_hb_material(cls, material):
        """Create a MassMaterial from a honeybee energy material."""
        assert isinstance(material, EnergyMaterial), \
            'Expected EnergyMaterial. Got {}.'.format(type(material))

        return cls(_name=short_name(material.display_name, 32),
                   _thickness=unit_convertor([material.thickness],
                                             'ft', 'm'),
                   _conductivity=unit_convertor(
                       [material.conductivity],
                       'Btu/h-ft2', 'W/m2'),
                   _density=round(material.density / 16.018, 3),

                   _specific_heat=unit_convertor(
                       [material.specific_heat],
                       'Btu/lb', 'J/kg'))

    def to_inp(self):
        spc = ''
        obj_lines = []

        obj_lines.append('\n"{self.name}" = MATERIAL'.format(self=self))
        obj_lines.append('\n   TYPE            = {}'.format(MaterialType.mass.value))
        obj_lines.append('\n   THICKNESS       = {self.thickness}'.format(self=self))
        obj_lines.append('\n   CONDUCTIVITY    = {self.conductivity}'.format(self=self))
        obj_lines.append('\n   DENSITY         = {self.density}'.format(self=self))
        obj_lines.append('\n   SPECIFIC-HEAT   = {self.specific_heat}'.format(self=self))
        obj_lines.append('\n  ..\n')

        return spc.join([l for l in obj_lines])

    def __repr__(self):
        return self.to_inp()


class Material:
    """Do2 Material object.
    refer to:
        assets/DOE22Vol2-Dictionary_48r.pdf pg: 97
    """

    def __init__(self, _material):
        self._material = _material

    @property
    def material(self):
        return self._material

    @classmethod
    def from_hb_material(cls, material):
        if isinstance(material, EnergyMaterial):
            return MassMaterial.from_hb_material(material)
        elif isinstance(material, EnergyMaterialNoMass):
            return NoMassMaterial.from_hb_material(material)
        else:
            raise ValueError('{} type is not supported for materials.'.format(
                type(material)))

    def to_inp(self):
        return self.material.to_inp()

    def __repr__(self):
        return self.to_inp()
