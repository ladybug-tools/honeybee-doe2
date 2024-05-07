"""Test the translators for ProgramType to INP."""
from honeybee_energy.lib.programtypes import office_program

from honeybee_doe2.load import SPACE_KEYS, SETPOINT_KEYS, MECH_AIRFLOW_KEYS
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


def test_program_type_to_inp_mech_airflow():
    """Test the ProgramType inp writer with mechanical airflow values in user_data."""
    office_with_airflow = office_program.duplicate()
    airflow_data = {
        "ASSIGNED-FLOW": 10.0,  # number in cfm
        "FLOW/AREA": 1.0,  # number in cfm/ft2
        "MIN-FLOW-RATIO": 0.3, # number between 0 and 1
        "MIN-FLOW/AREA": 0.3, # number in cfm/ft2
        "HMAX-FLOW-RATIO": 0.3  # number between 0 and 1
    }
    office_with_airflow.user_data = airflow_data

    switch_dict = program_type_to_inp(office_with_airflow)
    for key in MECH_AIRFLOW_KEYS:
        assert key in switch_dict

    inp_zone_switch = switch_dict_to_zone_inp(switch_dict)

    flow_per_area_str = \
        'SET-DEFAULT FOR ZONE\n' \
        '   TYPE = CONDITIONED\n' \
        '   FLOW/AREA =\n' \
        '{switch(#LR("SPACE", "C-ACTIVITY-DESC"))\n' \
        'case "rgrm": 1.0\n' \
        'default: no_default\n' \
        'endswitch}\n' \
        '..'
    assert flow_per_area_str in inp_zone_switch

    min_flow_ratio_str = \
        'SET-DEFAULT FOR ZONE\n' \
        '   TYPE = CONDITIONED\n' \
        '   MIN-FLOW-RATIO =\n' \
        '{switch(#LR("SPACE", "C-ACTIVITY-DESC"))\n' \
        'case "rgrm": 0.3\n' \
        'default: no_default\n' \
        'endswitch}\n' \
        '..'
    assert min_flow_ratio_str in inp_zone_switch

    min_flow_per_area_str = \
        'SET-DEFAULT FOR ZONE\n' \
        '   TYPE = CONDITIONED\n' \
        '   MIN-FLOW/AREA =\n' \
        '{switch(#LR("SPACE", "C-ACTIVITY-DESC"))\n' \
        'case "rgrm": 0.3\n' \
        'default: no_default\n' \
        'endswitch}\n' \
        '..'
    assert min_flow_per_area_str in inp_zone_switch

    hmax_flow_ratio_str = \
        'SET-DEFAULT FOR ZONE\n' \
        '   TYPE = CONDITIONED\n' \
        '   HMAX-FLOW-RATIO =\n' \
        '{switch(#LR("SPACE", "C-ACTIVITY-DESC"))\n' \
        'case "rgrm": 0.3\n' \
        'default: no_default\n' \
        'endswitch}\n' \
        '..'
    assert hmax_flow_ratio_str in inp_zone_switch
