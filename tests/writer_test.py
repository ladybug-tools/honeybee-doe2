import pathlib

from honeybee_doe2.writer import honeybee_model_to_inp
from honeybee.model import Model


def test_hbjson_translate():
    """Test translating a HBJSON file to an inp file."""
    hb_json = 'tests\\assets\\cubes.hbjson'
    out_inp = 'tests\\assets\\sample_out'
    out_file = pathlib.Path(out_inp, 'test_model.inp')
    # delete if exist
    if out_file.exists():
        out_file.unlink()
    hb_model = Model.from_file(hb_json)
    honeybee_model_to_inp(hb_model, folder=out_inp, name='test_model.inp')

    assert out_file.exists()
    # out_file.unlink()
