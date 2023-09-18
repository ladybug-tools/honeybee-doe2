import os

from click.testing import CliRunner
from ladybug.futil import nukedir

from honeybee_doe2.cli.translate import hb_model_to_inp_file


def test_model_to_folder():
    runner = CliRunner()
    input_hb_model = './tests/assets/shade_test.hbjson'
    folder = './tests/assets/sample_out'
    name = 'cli_test'
    hvac_mapping = 'story'

    result = runner.invoke(
        hb_model_to_inp_file,
        [input_hb_model, '--hvac_mapping', hvac_mapping, '--name', name, '--folder', folder])

    assert result.exit_code == 0
    assert os.path.isfile(os.path.join(folder, f'{name}.inp'))
    nukedir(folder, True)
