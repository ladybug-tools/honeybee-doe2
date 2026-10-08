"""Test the reader functions."""
import os

from honeybee.model import Model
from honeybee_energy.programtype import ProgramType
from honeybee_doe2.reader import command_dict_from_inp, model_from_inp_file
from honeybee_doe2.programtype import program_type_from_inp
from honeybee_doe2.util import find_user_lib_file


def test_parse_inp_file():
    """Test parsing of a DOE-2 INP file into object dict."""
    inp_file_path = os.path.join(os.path.dirname(__file__), 'assets',
                                 'school_project_from_wiz.inp')
    with open(inp_file_path, 'r') as doe_file:
        inp_content = doe_file.read()
    inp_object_dict = command_dict_from_inp(inp_content)

    assert isinstance(inp_object_dict, dict)
    assert 'PARAMETER' in inp_object_dict or len(inp_object_dict) > 0

    assert 'SPACE' in inp_object_dict
    assert isinstance(inp_object_dict['SPACE'], dict)
    assert len(inp_object_dict['SPACE']) > 0

    known_space = 'L1WNE Perim Spc (G.NE1)'
    assert known_space in inp_object_dict['SPACE']

    space_obj = inp_object_dict['SPACE'][known_space]
    assert isinstance(space_obj, dict)


def test_convert_underground_from_wiz():
    """Test converting an underground space from wizard to HBJSON."""
    inp_path = os.path.join(os.path.dirname(__file__), 'assets',
                            'underground_from_wiz.inp')
    model = model_from_inp_file(inp_path)
    assert isinstance(model, Model)


def test_convert_stacked_rect_from_wiz():
    """Test converting stacked rectangular geometry from wizard to HBJSON."""
    inp_path = os.path.join(os.path.dirname(__file__), 'assets', 
                            'stacked_rect_from_wiz.inp')
    model = model_from_inp_file(inp_path)
    assert isinstance(model, Model)


def test_convert_square_from_hbjson():
    """Test converting square geometry from HBJSON back to HBJSON."""
    inp_path = os.path.join(os.path.dirname(__file__), 'assets', 
                            'square_from_hbjson.inp')
    model = model_from_inp_file(inp_path)
    assert isinstance(model, Model)


def test_convert_stacked_squa_from_hbjson():
    """Test converting stacked square geometry from HBJSON back to HBJSON."""
    inp_path = os.path.join(os.path.dirname(__file__), 'assets', 
                            'stacked_squa_from_hbjson.inp')
    model = model_from_inp_file(inp_path)
    assert isinstance(model, Model)


def test_convert_sloped_roof_from_hbjson():
    """Test converting sloped roof geometry from HBJSON back to HBJSON."""
    inp_path = os.path.join(os.path.dirname(__file__), 'assets',
                            'sloped_roof_from_hbjson.inp')
    model = model_from_inp_file(inp_path)
    assert isinstance(model, Model)


def test_school_project_from_wiz():
    """Test full school project from wizard to HBJSON."""
    inp_path = os.path.join(os.path.dirname(__file__), 'assets',
                            'school_project_from_wiz.inp')
    model = model_from_inp_file(inp_path)
    assert isinstance(model, Model)


def test_set_defaults_assigned_loads():
    """Test parsing SET-DEFAULT blocks from an INP with directly assigned
    loads."""
    inp_path = os.path.join(os.path.dirname(__file__), 'assets',
                            'int_loads_assigned.inp')
    with open(inp_path, 'r') as f:
        inp_content = f.read()
    cmd_dict = command_dict_from_inp(inp_content)

    defaults = cmd_dict.get('DEFAULTS', {})
    assert len(defaults) > 0

    # SYSTEM defaults keyed by (command, TYPE)
    sys_d = defaults[('SYSTEM', 'PSZ')]
    assert sys_d['TYPE'] == 'PSZ'
    assert sys_d['HEAT-SOURCE'] == 'NONE'
    assert sys_d['RETURN-AIR-PATH'] == 'DIRECT'
    assert sys_d['COOL-FT-MIN'] == 70.0

    # ZONE defaults keyed by (command, TYPE)
    zone_d = defaults[('ZONE', 'CONDITIONED')]
    assert zone_d['TYPE'] == 'CONDITIONED'
    assert zone_d['BASEBOARD-CTRL'] == 'THERMOSTATIC'
    assert zone_d['AUX-HEAT-RATIO'] == 0.6


def test_set_defaults_case_switch_loads():
    """Test parsing SET-DEFAULT blocks with switch statements."""
    inp_path = os.path.join(os.path.dirname(__file__), 'assets',
                            'int_loads_case_switch.inp')
    with open(inp_path, 'r') as f:
        inp_content = f.read()
    cmd_dict = command_dict_from_inp(inp_content)

    defaults = cmd_dict.get('DEFAULTS', {})
    assert len(defaults) > 0

    # Multiple SPACE SET-DEFAULT blocks should merge into one
    space_d = defaults[('SPACE', '')]
    assert 'AREA/PERSON' in space_d
    assert 'PEOPLE-SCHEDULE' in space_d
    assert 'LIGHTING-W/AREA' in space_d
    assert 'EQUIPMENT-W/AREA' in space_d
    assert 'INF-FLOW/AREA' in space_d
    assert 'INF-METHOD' in space_d
    assert space_d['INF-METHOD'] == 'AIR-CHANGE'

    # Switch block values should contain the full switch text
    area_val = space_d['AREA/PERSON']
    assert 'switch' in area_val
    assert 'case "npln": 215.198' in area_val
    assert 'endswitch' in area_val


def test_program_type_from_inp_assigned():
    """Test building ProgramTypes from an INP with assigned loads
    per SPACE command"""
    inp_path = os.path.join(os.path.dirname(__file__), 'assets',
                            'int_loads_assigned.inp')
    with open(inp_path, 'r') as f:
        inp_content = f.read()
    
    cmd_dict = command_dict_from_inp(inp_content)

    lib_path = find_user_lib_file()
    if lib_path is None:
        return  # skip test if no library file found
    prog_types = program_type_from_inp(cmd_dict, lib_path)

    assert len(prog_types) > 0
    assert all(isinstance(pt, ProgramType) for pt in prog_types)

    # find the Office program type
    office = next((pt for pt in prog_types if 'Office' in pt.display_name),
                  None)
    assert office is not None
    assert office.people is not None
    assert office.people.area_per_person > 0
    assert office.lighting is not None
    assert office.lighting.watts_per_area > 0
    assert office.setpoint is not None


def test_program_type_from_inp_case_switch():
    """Test building ProgramTypes from an INP with switch-based defaults"""
    inp_path = os.path.join(os.path.dirname(__file__), 'assets',
                            'int_loads_case_switch.inp')
    with open(inp_path, 'r') as f:
        inp_content = f.read()
    cmd_dict = command_dict_from_inp(inp_content)
    prog_types = program_type_from_inp(cmd_dict)

    assert len(prog_types) > 0
    assert all(isinstance(pt, ProgramType) for pt in prog_types)

    # the case_switch file has activities: npln, m5m2, mthr
    display_names = {pt.display_name for pt in prog_types}
    assert 'Office' in display_names or 'npln' in display_names \
        or any('Office' in n or 'npln' in n for n in display_names)

    # check that space-level loads resolved from switch defaults
    for pt in prog_types:
        if pt.people is not None:
            assert pt.people.area_per_person > 0
        if pt.lighting is not None:
            assert pt.lighting.watts_per_area > 0
