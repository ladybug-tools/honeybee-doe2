import pathlib

from honeybee_doe2.writer import honeybee_model_to_inp
from honeybee.model import Model

def test_duplicate_names():
    """Test writiting inp with rooms having duplicate names"""
    hb_json = "./tests/assets/2023_rac_advanced_sample_project.hbjson"
    out_inp = './tests/assets/sample_out'
    out_file = pathlib.Path(out_inp, 'rac_test_model.inp')
    # delete if exists
    if out_file.exists():
        out_file.unlink()
    hb_model = Model.from_file(hb_json)
    honeybee_model_to_inp(hb_model, hvac_mapping='model', exclude_interior_walls=False, 
                          exclude_interior_ceilings=False,switch_statements=[],
                          folder=out_inp, name='rac_test_model.inp')

    assert out_file.exists()
    out_file.unlink()