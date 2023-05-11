import os

from click.testing import CliRunner
from ladybug.futil import nukedir

from honeybee_doe2.cli.translate import hb_model_to_inp_file
from honeybee.model import Model


def test_model_to_folder():
    runner = CliRunner()
    input_hb_model = './assets/cubes.hbjson'
    folder = '.assets/sample_out'
    name = 'cli_test'

    result = runner.invoke(
        hb_model_to_inp_file,
        [input_hb_model, '--name', name, '--folder', folder])

    assert result.exit_code == 0
    assert os.path.isfile(os.path.join(folder, f'{name}.inp'))
    #nukedir(folder, True)
