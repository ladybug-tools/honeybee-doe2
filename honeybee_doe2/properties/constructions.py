from enum import unique

from honeybee_energy.construction.opaque import OpaqueConstruction as OpConstr
from .materials import Material
from .inputils.blocks import mats_layers
from ..utils.doe_formatters import short_name, unit_convertor


class Construction:
    def __init__(self, _name, _materials, _absorptance, _roughness):

        self._name = _name
        self._materials = _materials
        self._absorptance = _absorptance
        self._roughness = _roughness

    @property
    def name(self):
        return short_name(self._name, 30)

    @property
    def materials(self):
        return self._materials

    @property
    def absorptance(self):
        return self._absorptance

    @property
    def roughness(self):
        return self._roughness

    @classmethod
    def from_hb_construction(cls, construction):
        """Creates inp construction from HB construction."""

        roughdict = {'VeryRough': 1, 'Rough': 2, 'MediumRough': 3,
                     'MediumSmooth': 4, 'Smooth': 5, 'VerySmooth': 6}

        materials = [Material.from_hb_material(material)
                     for material in construction.materials
                     ]
        absorptance = construction.materials[0].solar_absorptance
        roughness = roughdict[construction.materials[0].roughness]
        cons_name = construction.display_name

        return cls(cons_name, materials, absorptance, roughness)

    def to_inp(self, include_materials=True):
        if include_materials:

            block = ['\n'.join(material.to_inp() for material in self.materials)]
            materials = '\n    '.join(['"{}",'.format(material.name)
                                       for material in self.materials])

            objlines = []
            objlines.append('{} = LAYERS\n'.format('"{}_l"'.format(self.name)))

            objlines.append(
                '\n   MATERIAL             = (\n      {}\n   )\n'.format(
                    materials[: -1],
                    ','))

            objlines.append('\n   ..\n\n')
            objlines.append('\n"{self.name}_c" = CONSTRUCTION'.format(self=self))
            objlines.append('\n   TYPE                 = LAYERS\n')
            objlines.append(
                '\n   ABSORPTANCE          = {self.absorptance}'.format(self=self))
            objlines.append(
                '\n   ROUGHNESS            = {self.roughness}'.format(self=self))
            objlines.append('\n   LAYERS               = {layers_name}'.format(
                layers_name='"{}_l"'.format(self.name)))
            objlines.append('\n   ..\n')

            constr = ''
            construction = constr.join([l for l in objlines])
            block.append(construction)

            return '\n\n'.join(block)


class ConstructionCollection:
    """Construction object. Contains, materials and layers for *.inp file.
        Returns:
          $  Materials / Layers / Constructions *.inp block
    """

    def __init__(self, _constructions):
        self.constructions = _constructions

    @property
    def constructions(self):
        return self.constructions

    @classmethod
    def from_hb_constructions(cls, constructions):
        """Creates inp constructions from HB constructions."""
        unique_constructions = {
            construction.display_name: construction for construction in constructions
        }.values()

        constructions = [Construction.from_hb_construction(construction)
                         for construction in unique_constructions]
        return cls(constructions)

    def to_inp(self):

        block = [mats_layers]

        materials = set(
            mat.to_inp()
            for construction in self.constructions
            for mat in construction.materials
        )
        block.append('\n\n'.join(materials))

        # add constructions - layers are created as part of each construction definition
        for construction in self.constructions:
            block.append(construction.to_inp(include_materials=False))

        return '\n'.join(block)

    def __repr__(self):
        return self.to_inp()
