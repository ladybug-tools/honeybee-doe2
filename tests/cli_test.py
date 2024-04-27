"""Test the CLI commands"""

import os
from click.testing import CliRunner

from honeybee_doe2.cli.translate import model_to_inp_file


def test_model_to_inp_cli():
    runner = CliRunner()
    input_hb_model = './tests/assets/shade_test.hbjson'
    out_file = './tests/assets/cli_test.inp'
    hvac_mapping = 'Story'

    in_args = [
        input_hb_model, '--hvac-mapping', hvac_mapping,
        '--exclude-interior-walls',  '--exclude-interior-ceilings',
        '--output-file', out_file]
    result = runner.invoke(model_to_inp_file, in_args)

    assert result.exit_code == 0
    assert os.path.isfile(out_file)
    os.remove(out_file)