"""Test the translators for ProgramType to INP."""
from honeybee_energy.lib.programtypes import office_program, program_type_by_identifier

from honeybee_doe2.load import SPACE_KEYS, SETPOINT_KEYS
from honeybee_doe2.programtype import program_type_to_inp, switch_dict_to_space_inp, \
    switch_dict_to_zone_inp


def test_program_type_to_inp():
    """Test the basic functionality of the ProgramType inp writer."""
    switch_dict = program_type_to_inp(office_program)

    for key in SPACE_KEYS:
        if key not in ('LIGHTING-SCHEDULE', 'INF-METHOD'):
            assert key in switch_dict
    for key in SETPOINT_KEYS:
        assert key in switch_dict

    inp_space_switch = switch_dict_to_space_inp(switch_dict)
    st_str = \
        'SET-DEFAULT FOR SPACE\n' \
        '   AREA/PERSON =\n' \
        '{switch(#L("C-ACTIVITY-DESC"))\n' \
        'case "rgrm": 190.512\n' \
        'default: no_default\n' \
        'endswitch}\n' \
        '..\n'
    assert inp_space_switch.startswith(st_str)

    inp_zone_switch = switch_dict_to_zone_inp(switch_dict)
    st_str = \
        'SET-DEFAULT FOR ZONE\n' \
        '   TYPE = CONDITIONED\n' \
        '   DESIGN-HEAT-T =\n' \
        '{switch(#LR("SPACE", "C-ACTIVITY-DESC"))\n' \
        'case "rgrm": 69.8\n' \
        'default: no_default\n' \
        'endswitch}\n' \
        '..'
    assert inp_zone_switch.startswith(st_str)
