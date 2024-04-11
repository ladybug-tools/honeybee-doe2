from enum import unique

from honeybee_energy.construction.opaque import OpaqueConstruction as OpConstr
from .materials import Material, NoMassMaterial, MassMaterial
from .inputils.blocks import mats_layers
from ..utils.doe_formatters import short_name, unit_convertor
from honeybee_energy.material.opaque import EnergyMaterial, EnergyMaterialNoMass
from dataclasses import dataclass
from typing import List

@dataclass
class UvalueConstruction:
    name: str
    u_value: float 
    
    @classmethod
    def from_hb_construction(cls, construction:OpConstr):
        name = short_name(construction.display_name, 30)
        u_value = construction.u_value
        return cls(name=name, u_value=u_value)
    
    def to_inp(self, include_materials=False):
        objlines = []
        objlines.append(f'"{self.name}_c" = CONSTRUCTION\n')
        objlines.append('TYPE           = U-VALUE\n')
        objlines.append(f'U-VALUE        = {self.u_value}\n..\n')
        result = ''.join([l for l in objlines])
        return result
        
    def __repr__ (self):
        return self.to_inp()

@dataclass
class Construction:
    name: str
    materials: List[Material]
    absorptance: float
    roughness: int

    @classmethod
    def from_hb_construction(cls, construction: OpConstr):
        """Create inp construction from HB construction."""
        roughdict = {'VeryRough': 1, 'Rough': 2, 'MediumRough': 3,
                     'MediumSmooth': 4, 'Smooth': 5, 'VerySmooth': 6}
        if not isinstance(construction, OpConstr):
            # this should raise an error but for now I leave it to print until we
            # support a handful number of types
            print(
                f'Unsupported Construction type: {type(construction)}.\n'
                'Please be patient as more features and capabilities are implemented.'
            )
            return cls(construction.display_name, [], 0, 0)

        materials = []
        for material in construction._materials:
            if material.thickness <= 0.003:
                materials.append(NoMassMaterial.from_hb_material(material))
            elif material.thickness > 0.003:
                materials.append(Material.from_hb_material(material))
        
        
        absorptance = construction.materials[0].solar_absorptance
        roughness = roughdict[construction.materials[0].roughness]

        cons_name = short_name(construction.display_name, 30)

        return cls(cons_name, materials, absorptance, roughness)

    def to_inp(self, include_materials=True):

        # temporary solution not return values for unsupported construction types
        if not self.materials:
            return ''

        if include_materials:
            block = ['\n'.join(material.to_inp() for material in self.materials)]
        else:
            block = []
    

        materials = '\n      '.join(f'"{material.name}",'
                                    for material in self.materials)

        layers_name = f'"{self.name}_l"'
        construction = f'{layers_name} = LAYERS\n' \
            f'   MATERIAL             = (\n      {materials[:-1]}\n   )\n' \
            '   ..\n\n' \
            f'"{self.name}_c" = CONSTRUCTION\n' \
            '   TYPE                 = LAYERS\n' \
            f'   ABSORPTANCE          = {self.absorptance}\n' \
            f'   ROUGHNESS            = {self.roughness}\n' \
            f'   LAYERS               = {layers_name}\n' \
            '   ..\n'
        block.append(construction)

        return '\n\n'.join(block)

    def __repr__(self) -> str:
        return self.to_inp()


@dataclass
class ConstructionCollection:
    """Construction object. Contains, materials and layers for *.inp file.

        Returns:
          $  Materials / Layers / Constructions *.inp block
    """
    constructions: List[Construction]

    @classmethod
    def from_hb_constructions(cls, constructions: List[OpConstr]):
        unique_constructions = {
            construction.display_name: construction for construction in constructions
        }.values()

        constructions = []
        for construction in unique_constructions:
            if construction.thickness > 0.003:
                constructions.append(Construction.from_hb_construction(construction))
            elif construction.thickness < 0.003:
                constructions.append(UvalueConstruction.from_hb_construction(construction))
        
        return cls(constructions)

    def to_inp(self):

        block = []

        # collect all the materials and ensure to only include the unique ones
        materials = set()
        
        for construction in self.constructions:
            if isinstance(construction, Construction):
                for mat in construction.materials:
                    materials.add(mat.to_inp())
        
        block.append(''.join(materials))

        # add constructions - layers are created as part of each construction definition
        for construction in self.constructions:
            block.append(construction.to_inp(include_materials=False))

        return '\n'.join(block)

    def __repr__(self):
        return self.to_inp()