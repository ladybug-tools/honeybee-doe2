import pathlib

from honeybee_doe2.writer import honeybee_model_to_inp
from honeybee.model import Model



def test_switch_true():
    """Test writiting inp with switch_statements"""
    hb_json = "./tests/assets/switch_with_user_data.hbjson"
    out_inp = './tests/assets/sample_out'
    out_file = pathlib.Path(out_inp, 'switch_true_test_model.inp')
    # delete if exists
    if out_file.exists():
        out_file.unlink()
    hb_model = Model.from_file(hb_json)
    honeybee_model_to_inp(hb_model, hvac_mapping='model', exclude_interior_walls=False, 
                          exclude_interior_ceilings=False,switch_statements=True,
                          folder=out_inp, name='switch_true_test_model.inp')

    assert out_file.exists()
    #out_file.unlink()

def test_switch_false():
    """Test writiting inp with switch_statements"""
    hb_json = "./tests/assets/testbed_no_user_data.hbjson"
    out_inp = './tests/assets/sample_out'
    out_file = pathlib.Path(out_inp, 'switch_false_test_model.inp')
    # delete if exists
    if out_file.exists():
        out_file.unlink()
    hb_model = Model.from_file(hb_json)
    honeybee_model_to_inp(hb_model, hvac_mapping='model', exclude_interior_walls=False, 
                          exclude_interior_ceilings=False, switch_statements=False,
                          folder=out_inp, name='switch_false_test_model.inp')

    assert out_file.exists()
    #out_file.unlink()














