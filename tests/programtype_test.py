import pathlib

from honeybee_doe2.writer import honeybee_model_to_inp
from honeybee.model import Model


def test_model_with_program_types():
    hb_json = './tests/assets/revit-sample-with-program-type.hbjson'
    out_inp = './tests/assets/sample_out'
    out_file = pathlib.Path(out_inp, 'test_model_w_pt.inp')
    if out_file.exists():
        out_file.unlink()
    hb_model = Model.from_file(hb_json)
    honeybee_model_to_inp(hb_model, hvac_mapping='story',
                          folder=out_inp, name='test_model_w_pt.inp')
    
    assert out_file.exists()
    #out_file.unlink()
