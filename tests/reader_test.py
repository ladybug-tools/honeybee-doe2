"""Test the reader functions."""
import os

from honeybee.model import Model
from honeybee_doe2.reader import command_dict_from_inp, model_from_inp_file


def test_parse_inp_file():
    """Test parsing of a DOE-2 INP file into object dict."""
    inp_file_path = os.path.join(os.path.dirname(__file__), 'assets', 'school_project_from_wiz.inp')
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
    inp_path = os.path.join(os.path.dirname(__file__), 'assets', 'underground_from_wiz.inp')
    model = model_from_inp_file(inp_path)
    assert isinstance(model, Model)


def test_convert_stacked_rect_from_wiz():
    """Test converting stacked rectangular geometry from wizard to HBJSON."""
    inp_path = os.path.join(os.path.dirname(__file__), 'assets', 'stacked_rect_from_wiz.inp')
    model = model_from_inp_file(inp_path)
    assert isinstance(model, Model)


def test_convert_square_from_hbjson():
    """Test converting square geometry from HBJSON back to HBJSON."""
    inp_path = os.path.join(os.path.dirname(__file__), 'assets', 'square_from_hbjson.inp')
    model = model_from_inp_file(inp_path)
    assert isinstance(model, Model)


def test_convert_stacked_squa_from_hbjson():
    """Test converting stacked square geometry from HBJSON back to HBJSON."""
    inp_path = os.path.join(os.path.dirname(__file__), 'assets', 'stacked_squa_from_hbjson.inp')
    model = model_from_inp_file(inp_path)
    assert isinstance(model, Model)


def test_convert_sloped_roof_from_hbjson():
    """Test converting sloped roof geometry from HBJSON back to HBJSON."""
    inp_path = os.path.join(os.path.dirname(__file__), 'assets', 'sloped_roof_from_hbjson.inp')
    model = model_from_inp_file(inp_path)
    assert isinstance(model, Model)


def test_school_project_from_wiz():
    """Test full school project from wizard to HBJSON."""
    inp_path = os.path.join(os.path.dirname(__file__), 'assets', 'school_project_from_wiz.inp')
    model = model_from_inp_file(inp_path)
    assert isinstance(model, Model)
