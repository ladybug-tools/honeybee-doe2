"""Test the CLI commands"""
import json
import os
from click.testing import CliRunner

from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_doe2.cli.translate import model_to_inp_cli, model_from_inp_cli, \
    schedules_from_inp_cli, schedules_to_inp_cli, constructions_to_inp_cli, \
    materials_from_inp_cli, constructions_from_inp_cli


def test_model_to_inp_cli():
    """Test the translation of a Model to INP."""
    runner = CliRunner()
    input_hb_model = './tests/assets/shade_test.hbjson'
    out_file = './tests/assets/cli_test.inp'
    hvac_mapping = 'Story'

    in_args = [
        input_hb_model, '--hvac-mapping', hvac_mapping,
        '--exclude-interior-walls',  '--exclude-interior-ceilings',
        '--output-file', out_file]
    result = runner.invoke(model_to_inp_cli, in_args)

    assert result.exit_code == 0
    assert os.path.isfile(out_file)

    result = runner.invoke(model_from_inp_cli, [out_file])
    assert result.exit_code == 0
    os.remove(out_file)


def test_schedule_to_from_inp():
    runner = CliRunner()
    input_hb_sch = './tests/assets/Schedules.inp'

    result = runner.invoke(schedules_from_inp_cli, [input_hb_sch, '--array'])
    assert result.exit_code == 0
    result_dict = json.loads(result.output)
    schedules = [ScheduleRuleset.from_dict(sch) for sch in result_dict]
    assert len(schedules) >= 36

    output_hb_json = './tests/assets/schedules.json'
    result = runner.invoke(
        schedules_from_inp_cli, [input_hb_sch, '--output-file', output_hb_json])
    assert result.exit_code == 0
    assert os.path.isfile(output_hb_json)

    result = runner.invoke(schedules_to_inp_cli, [output_hb_json])
    assert result.exit_code == 0

    os.remove(output_hb_json)


def test_constructions_to_from_inp():
    runner = CliRunner()
    input_hb_constr = './tests/assets/small_revit_sample.inp'

    result = runner.invoke(materials_from_inp_cli, [input_hb_constr])
    assert result.exit_code == 0

    result = runner.invoke(constructions_from_inp_cli, [input_hb_constr])
    assert result.exit_code == 0

    output_hb_json = './tests/json/GlzSys_Triple_Clear_Avg.json'
    result = runner.invoke(
        constructions_from_inp_cli, [input_hb_constr, '--output-file', output_hb_json])
    assert result.exit_code == 0
    assert os.path.isfile(output_hb_json)

    result = runner.invoke(constructions_to_inp_cli, [output_hb_json])
    assert result.exit_code == 0

    os.remove(output_hb_json)
