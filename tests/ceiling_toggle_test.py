import pathlib

from honeybee_doe2.writer import honeybee_model_to_inp
from honeybee.model import Model

hvac_test = './tests/assets/multi_hvac.hbjson'
standard_test = './tests/assets/2023_rac_advanced_sample_project.hbjson'
air_wall_test = './tests/assets/Air_Wall_test.hbjson'
ceiling_adj_test = './tests/assets/ceiling_adj_test.hbjson'

def test_hbjson_translate():
    """Test translating a HBJSON file to an inp file."""
    hb_json = ceiling_adj_test

    out_inp = './tests/assets/sample_out'
    out_file = pathlib.Path(out_inp, 'ceiling_test_model.inp')
    # delete if exists
    if out_file.exists():
        out_file.unlink()
    hb_model = Model.from_file(hb_json)
    honeybee_model_to_inp(hb_model, hvac_mapping='model', exclude_interior_walls=False, exclude_interior_ceilings=True,
                          folder=out_inp, name='ceiling_test_model.inp')

    assert out_file.exists()
    out_file.unlink()