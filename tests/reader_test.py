"""Test the reader functions."""
import os
from honeybee_doe2.reader import command_dict_from_inp, model_from_inp
from honeybee.model import Model


def test_parse_inp_file():
    """Test parsing of a DOE-2 INP file into object dict"""
    #inp_file_path = './tests/assets/test_project.inp'
    inp_file_path = os.path.join(os.path.dirname(__file__), 'assets', 'test_project.inp')
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


inp_file_path = os.path.join(os.path.dirname(__file__), 'assets', 'sloped_roof_from_hbjson.inp')
model = model_from_inp(inp_file_path)

model.to_hbjson(r'C:\Users\Steve.marentette.IG\Desktop\doe\out.hbjson')