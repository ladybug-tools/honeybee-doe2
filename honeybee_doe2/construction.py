"""honeybee-inp construction translators."""
from __future__ import division
import os
import re

from ladybug.datatype.uvalue import UValue
from ladybug.datatype.rvalue import RValue
from ladybug.datatype.distance import Distance
from honeybee.typing import clean_doe2_string
from honeybee_energy.material.opaque import EnergyMaterial, EnergyMaterialNoMass
from honeybee_energy.material.glazing import EnergyWindowMaterialSimpleGlazSys
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.window import WindowConstruction

from .config import RES_CHARS, MIN_LAYER_THICKNESS
from .util import generate_inp_string, generate_inp_string_list_format, \
    parse_inp_string, clean_inp_file_contents

# dictionary to map between E+ and DOE-2 roughness types
ROUGHNESS_MAP = {
    'VeryRough': 1, 'Rough': 2, 'MediumRough': 3,
    'MediumSmooth': 4, 'Smooth': 5, 'VerySmooth': 6
}


def opaque_material_to_inp(material):
    """Convert an EnergyMaterial or EnergyMaterialNoMass into a MATERIAL INP string.

    Note that EnergyMaterials that are below a certain thickness will be automatically
    converted to No Mass materials for compatibility with DOE-2. Also note that
    this does not work for any materials that can be a part of a window constructions.
    """
    doe2_id = clean_doe2_string(material.identifier, RES_CHARS)
    # check if the material should be translated as a no mass material
    if isinstance(material, EnergyMaterialNoMass) or \
            material.thickness < MIN_LAYER_THICKNESS:
        r_val = RValue().to_unit([material.r_value], 'h-ft2-F/Btu', 'm2-K/W')[0]
        keywords = ('TYPE', 'RESISTANCE')
        values = ('RESISTANCE', round(r_val, 6))
        return generate_inp_string(doe2_id, 'MATERIAL', keywords, values)
    # write out detailed properties for the material
    thickness = round(Distance().to_unit([material.thickness], 'ft', 'm')[0], 3)
    conduct = round(material.conductivity * 0.578176, 3)  # convert to BTU/h-ft-F
    density = round(material.density / 16.018, 3)  # convert to lb/ft3
    spec_en = round(material.specific_heat * 0.0002388459, 3)  # convert to BTU/lb-F
    keywords = ('TYPE', 'THICKNESS', 'CONDUCTIVITY', 'DENSITY', 'SPECIFIC-HEAT')
    values = ('PROPERTIES', thickness, conduct, density, spec_en)
    return generate_inp_string(doe2_id, 'MATERIAL', keywords, values)


def opaque_construction_to_inp(construction):
    """Convert an OpaqueConstruction into a CONSTRUCTION INP string.

    This will include both the LAYERS definition as well as the CONSTRUCTION but
    it does NOT include the constituent MATERIAL definitions and their properties.
    """
    doe2_id = clean_doe2_string(construction.identifier, RES_CHARS)
    # if the construction has no heat capacity, simply make a U-VALUE construction
    if construction.area_heat_capacity == 0 or \
            construction.thickness <= MIN_LAYER_THICKNESS * len(construction.materials):
        con_cond = UValue().to_unit([construction.u_factor], 'Btu/h-ft2-F', 'W/m2-K')[0]
        keywords = ('TYPE', 'U-VALUE')
        values = ('U-VALUE', round(con_cond, 6))
        return generate_inp_string(doe2_id, 'CONSTRUCTION', keywords, values)
    # create the specification of material layers
    layer_id = '{}_l'.format(doe2_id)
    layers = ['"{}"'.format(clean_doe2_string(mat, RES_CHARS))
              for mat in construction.layers]
    layer_str = generate_inp_string_list_format(
        layer_id, 'LAYERS', ['MATERIAL'], [layers])
    # create the construction specification
    roughness = ROUGHNESS_MAP[construction.materials[0].roughness]
    sol_absorb = round(1 - construction.outside_solar_reflectance, 3)
    keywords = ('TYPE', 'ABSORPTANCE', 'ROUGHNESS', 'LAYERS')
    values = ('LAYERS', sol_absorb, roughness, '"{}"'.format(layer_id))
    constr_str = generate_inp_string(doe2_id, 'CONSTRUCTION', keywords, values)
    return ''.join((layer_str, constr_str))


def window_construction_to_inp(construction):
    """Convert a WindowConstruction (or its variants) into a GLASS-TYPE INP string."""
    doe2_id = clean_doe2_string(construction.identifier, RES_CHARS)
    shading_coef = construction.shgc / 0.87
    glass_cond = UValue().to_unit([construction.u_factor], 'Btu/h-ft2-F', 'W/m2-K')[0]
    keywords = ('TYPE', 'SHADING-COEF', 'GLASS-CONDUCT')
    values = ('SHADING-COEF', round(shading_coef, 3), round(glass_cond, 6))
    return generate_inp_string(doe2_id, 'GLASS-TYPE', keywords, values)


def door_construction_to_inp(construction):
    """Convert an OpaqueConstruction or WindowConstruction to a CONSTRUCTION INP string.

    This translation pathway always uses a NoMass U-VALUE Construction.
    """
    doe2_id = clean_doe2_string(construction.identifier, RES_CHARS)
    constr_cond = UValue().to_unit([construction.u_factor], 'Btu/h-ft2-F', 'W/m2-K')[0]
    keywords = ('TYPE', 'U-VALUE')
    values = ('U-VALUE', round(constr_cond, 6))
    return generate_inp_string(doe2_id, 'CONSTRUCTION', keywords, values)


def air_construction_to_inp(construction):
    """Convert an AirBoundaryConstruction to a CONSTRUCTION INP string.

    This translation pathway always uses a NoMass U-VALUE Construction.
    """
    doe2_id = clean_doe2_string(construction.identifier, RES_CHARS)
    constr_cond = 1.0  # default U-Value in Btu/h-ft2-F
    keywords = ('TYPE', 'U-VALUE')
    values = ('U-VALUE', constr_cond)
    return generate_inp_string(doe2_id, 'CONSTRUCTION', keywords, values)


def opaque_material_from_inp(inp_string):
    """Create an EnergyMaterial or EnergyMaterialNoMass from a MATERIAL INP string."""
    # parse the string into properties
    u_name, command, keywords, values = parse_inp_string(inp_string)
    attr_dict = {key: val for key, val in zip(keywords, values)}
    # create the material object
    if attr_dict['TYPE'] == 'RESISTANCE':
        r_val = RValue().to_unit([float(attr_dict['RESISTANCE'])], 'm2-K/W', 'h-ft2-F/Btu')[0]
        return EnergyMaterialNoMass(u_name, round(r_val, 6))
    elif attr_dict['TYPE'] == 'PROPERTIES':
        thickness = Distance().to_unit([float(attr_dict['THICKNESS'])], 'm', 'ft')[0]
        conduct = float(attr_dict['CONDUCTIVITY']) / 0.578176  # convert from BTU/h-ft-F
        density = float(attr_dict['DENSITY']) * 16.018  # convert from lb/ft3
        spec_en = float(attr_dict['SPECIFIC-HEAT']) / 0.0002388459  # convert from BTU/lb-F
        return EnergyMaterial(
            u_name, round(thickness, 6), round(conduct, 3),
            round(density, 3), round(spec_en)
        )


def opaque_construction_from_inp(inp_string, layers, materials):
    """Create an OpaqueConstruction from INP text strings.

    Args:
        inp_string: A text string fully describing an EnergyPlus construction.
        layers: A dictionary with U-names of layers as keys and INP strings
            of LAYERS objects as values.
        materials: A dictionary with identifiers of materials as keys and Python
            material objects as values.
    """
    # parse the string into properties
    u_name, command, keywords, values = parse_inp_string(inp_string)
    attr_dict = {key: val for key, val in zip(keywords, values)}
    if 'TYPE' in attr_dict and attr_dict['TYPE'] == 'U-VALUE':
        # simple construction with one layer
        u_val = UValue().to_unit([float(attr_dict['U-VALUE'])], 'W/m2-K', 'Btu/h-ft2-F')[0]
        mat = EnergyMaterialNoMass('{}_Mat'.format(u_name), round(1 / u_val, 6))
        return OpaqueConstruction(u_name, [mat])

    # assemble the layers
    layers_id = attr_dict['LAYERS'].replace('"', '')
    try:
        layers_string = layers[layers_id]
        _, _, _, l_values = parse_inp_string(layers_string)
        try:
            l_values = eval(l_values[0], {})
            mats = [materials[m_id.replace('"', '')] for m_id in l_values]
        except KeyError as e:
            raise ValueError('Failed to find {} in the input materials dictionary.'.format(e))
    except KeyError as e:
        raise ValueError('Failed to find {} in the input layers dictionary.'.format(e))
    construction = OpaqueConstruction(u_name, mats)

    # apply any absorptance and roughness values and return the construction
    construction.materials[0].unlock()
    try:
        construction.materials[0].solar_absorptance = attr_dict['ABSORPTANCE']
    except Exception:  # no absorptance specified or material is locked
        pass
    try:
        inp_rough = int(attr_dict['ROUGHNESS'])
        for rk, rv in ROUGHNESS_MAP.items():
            if inp_rough == rv:
                construction.materials[0].roughness = rk
                break
    except Exception:  # no roughness specified or material is locked
        pass
    construction.materials[0].lock()
    return construction


def window_construction_from_inp(inp_string):
    """Create a WindowConstruction from a GLASS-TYPE INP string.

    Will be None if the GLASS-TYPE uses one of DOE-2's internal glass type codes.
    """
    # parse the string into properties
    u_name, command, keywords, values = parse_inp_string(inp_string)
    attr_dict = {key: val for key, val in zip(keywords, values)}
    if attr_dict['TYPE'] != 'SHADING-COEF':
        return None
    # create the material and construction objects
    shgc = round(float(attr_dict['SHADING-COEF']) * 0.87, 3)
    try:
        u_factor = float(attr_dict['GLASS-CONDUCT'])
    except KeyError:  # possibly using a newer format for specifying U-Value
        try:
            u_factor = float(attr_dict['GLASS-CONDUCTANCE'])
        except KeyError:
            return None
    u_factor = round(UValue().to_unit([u_factor], 'W/m2-K', 'Btu/h-ft2-F')[0], 6)
    keywords = ('TYPE', 'SHADING-COEF', 'GLASS-CONDUCT')
    mat = EnergyWindowMaterialSimpleGlazSys('{}_Mat'.format(u_name), u_factor, shgc)
    return WindowConstruction(u_name, [mat])


def extract_all_constructions_from_inp_file(inp_file):
    """Extract all ScheduleRuleset objects from a DOE-2 INP file.

    Args:
        inp_file: A path to an INP file containing objects for CONSTRUCTION,
            LAYERS, MATERIAL, and/or GLASS-TYPE.

    Returns:
        A tuple with three elements

            -   window_constructions: A list of all WindowConstruction objects in the INP
                file as honeybee_energy WindowConstruction objects.

            -   opaque_constructions: A list of all OpaqueConstruction objects in the IDF
                file as honeybee_energy OpaqueConstruction objects.

            -   materials: A list of all opaque materials in the IDF file as
                honeybee_energy EnergyMaterial or EnergyMaterialNoMass objects.
    """
    # read the file and remove lines of comments
    assert os.path.isfile(inp_file), 'Cannot find an INP file at: {}'.format(inp_file)
    with open(inp_file, 'r') as doe_file:
        inp_content = doe_file.read()
    file_contents = clean_inp_file_contents(inp_content)

    # extract all of the MATERIAL objects
    mat_pattern = re.compile(r'(?i)(".*=.*MATERIAL\n[\s\S]*?\.\.)')
    mat_strings = mat_pattern.findall(file_contents)
    mat_dict = {}
    for mat_str in mat_strings:
        mat_str = mat_str.strip()
        try:
            mat_obj = opaque_material_from_inp(mat_str)
            mat_dict[mat_obj.identifier] = mat_obj
        except Exception:
            pass  # not a material that can be converted
    materials = list(mat_dict.values())

    # extract all LAYERS objects
    layer_pattern = re.compile(r'(?i)(".*=.*LAYERS\n[\s\S]*?\.\.)')
    layer_strings = layer_pattern.findall(file_contents)
    layer_dict = {}
    for layer_str in layer_strings:
        layer_str = layer_str.strip()
        try:
            layer_id, _, _, _ = parse_inp_string(layer_str)
            layer_dict[layer_id] = layer_str
        except Exception:
            pass  # not a Layers object that can be converted

    # extract all CONSTRUCTION objects
    con_pattern = re.compile(r'(?i)(".*=.*CONSTRUCTION\n[\s\S]*?\.\.)')
    con_strings = con_pattern.findall(file_contents)
    opaque_constructions = []
    for con_str in con_strings:
        con_str = con_str.strip()
        try:
            con_obj = opaque_construction_from_inp(con_str, layer_dict, mat_dict)
            opaque_constructions.append(con_obj)
        except Exception:
            pass  # not a construction that can be converted

    # extract all GLASS-TYPE objects
    glass_pattern = re.compile(r'(?i)(".*=.*GLASS-TYPE\n[\s\S]*?\.\.)')
    glass_strings = glass_pattern.findall(file_contents)
    window_constructions = []
    for g_str in glass_strings:
        g_str = g_str.strip()
        try:
            con_obj = window_construction_from_inp(g_str)
            if con_obj is not None:
                window_constructions.append(con_obj)
        except Exception:
            pass  # not a construction that can be converted

    return window_constructions, opaque_constructions, materials
