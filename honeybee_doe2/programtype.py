"""honeybee-doe2 program type translators."""
from __future__ import division

from collections import defaultdict

from honeybee_energy.programtype import ProgramType
from honeybee.typing import clean_string

from .util import switch_statement_id, resolve_defaults, \
        child_objects_from_parent
from .load import VENTILATION_KEYS, people_to_inp, lighting_to_inp, electric_equipment_to_inp, \
    infiltration_to_inp, setpoint_to_inp, ventilation_to_inp, \
    people_from_inp, lighting_from_inp, electric_equipment_from_inp, \
    infiltration_from_inp, setpoint_from_inp, ventilation_from_inp, \
    SPACE_KEYS, ZONE_KEYS, SCHEDULE_KEYS, MECH_AIRFLOW_KEYS
from .schedule import build_schedule_dict, resolve_schedule
SCH_KEY_SET = set(SCHEDULE_KEYS)


def program_type_to_inp(program_type, switch_dict=None):
    """Translate a ProgramType into a dictionary used to write INP switch statements.

    Args:
        program_type: A honeybee-energy ProgramType definition.
        switch_dict: An optional dictionary with INP keywords as keys (such as
            PEOPLE-SCHEDULE or AREA/PERSON or LIGHTING-W/AREA). The values of the
            dictionary should be lists of switch statement text strings, such as
            'case "conf": #SI("Small Off Occ", "SPACE", "PEOPLE-SCHEDULE")'.
            Specifying an input dictionary here can be used to build up switch
            statements for all program types across a model.

    Returns:
        An dictionary with INP keywords as keys (such as PEOPLE-SCHEDULE or AREA/PERSON).
        The values of the dictionary are lists of switch statement text strings,
        such as 'case "conf": #SI("Small Off Occ", "SPACE", "PEOPLE-SCHEDULE")'.
    """
    # set up the switch statement dictionary to be filled
    switch_dict = switch_dict if switch_dict is not None else {}
    prog_uid = switch_statement_id(program_type.identifier)
    base_switch = 'case "{}": '.format(prog_uid)

    def _format_schedule(sch_key, sch_uid, obj_type='SPACE'):
        """Format schedules in the way they are written into switch statements."""
        return '{}#SI({}, "{}", "{}")'.format(base_switch, sch_uid, obj_type, sch_key)
    
    def _add_to_switch_dict(keyword, value):
        """Add a key: value pair to the switch dictionary with a check."""
        try:
            switch_dict[keyword].append(value)
        except KeyError:  # the first time this key was encountered in the dict
            switch_dict[keyword] = [value]

    # write the people into the dictionary
    ppl_kwd, ppl_val = people_to_inp(program_type.people)
    for key, val in zip(ppl_kwd, ppl_val):
        if key in SCH_KEY_SET:
            _add_to_switch_dict(key, _format_schedule(key, val, 'SPACE'))
        else:
            _add_to_switch_dict(key, '{}{}'.format(base_switch, val))

    # write the lighting into the dictionary
    lgt_kwd, lgt_val = lighting_to_inp(program_type.lighting)
    for key, val in zip(lgt_kwd, lgt_val):
        if key == 'LIGHTING-SCHEDULE':
            key = 'LIGHTING-SCHEDUL'  # there's a typo in DOE-2 that was never fixed
            _add_to_switch_dict(key, _format_schedule(key, val, 'SPACE'))
        else:
            _add_to_switch_dict(key, '{}{}'.format(base_switch, val))

    # write the equipment into the dictionary
    eq_kwd, eq_val = electric_equipment_to_inp(program_type.electric_equipment)
    for key, val in zip(eq_kwd, eq_val):
        if key in SCH_KEY_SET:
            _add_to_switch_dict(key, _format_schedule(key, val, 'SPACE'))
        else:
            _add_to_switch_dict(key, '{}{}'.format(base_switch, val))

    # write the infiltration into the dictionary
    inf_kwd, inf_val = infiltration_to_inp(program_type.infiltration)
    for key, val in zip(inf_kwd, inf_val):
        if key in SCH_KEY_SET:
            _add_to_switch_dict(key, _format_schedule(key, val, 'SPACE'))
        elif key == 'INF-METHOD':
            continue  # DOE-2 does not like when we define this key
        else:
            _add_to_switch_dict(key, '{}{}'.format(base_switch, val))

    # write the setpoint into the dictionary
    stp_kwd, stp_val = setpoint_to_inp(program_type.setpoint)
    for key, val in zip(stp_kwd, stp_val):
        if key in SCH_KEY_SET:
            _add_to_switch_dict(key, _format_schedule(key, val, 'ZONE'))
        else:
            _add_to_switch_dict(key, '{}{}'.format(base_switch, val))

    # write the ventilation into the dictionary
    vt_kwd, vt_val = ventilation_to_inp(program_type.ventilation)
    for key, val in zip(vt_kwd, vt_val):
        if key in SCH_KEY_SET:
            _add_to_switch_dict(key, _format_schedule(key, val, 'ZONE'))
        else:
            _add_to_switch_dict(key, '{}{}'.format(base_switch, val))

    # if the user_data of the ProgramType has Mech AirFlow keys, add them
    if program_type.user_data is not None:
        for air_key in MECH_AIRFLOW_KEYS:
            if air_key in program_type.user_data:
                val = program_type.user_data[air_key]
                _add_to_switch_dict(air_key, '{}{}'.format(base_switch, val))

    return switch_dict


def program_type_from_inp(cmd_dict, lib_file_path=None):
    """Create ProgramType objects from a parsed INP command dictionary.

    Spaces are grouped by their C-ACTIVITY-DESC attribute. For each unique
    activity description, a representative space and its linked zone are used
    to resolve SET-DEFAULT fallback values and build a ProgramType containing
    People, Lighting, ElectricEquipment, Infiltration, Setpoint, and
    Ventilation objects.

    Args:
        cmd_dict: The command dictionary returned by ``command_dict_from_inp``.
        lib_file_path: Optional path to eQUEST library file (eQ_Lib.dat) for
            resolving library schedules. If None, library schedules won't
            be resolved.

    Returns:
        A list of honeybee-energy ProgramType objects, one per unique
        C-ACTIVITY-DESC found in the model's spaces.
    """
    spaces = cmd_dict.get('SPACE', {})
    zones = cmd_dict.get('ZONE', {})
    systems = cmd_dict.get('SYSTEM', {})
    defaults = cmd_dict.get('DEFAULTS', {})
    day_schs = cmd_dict.get('DAY-SCHEDULE-PD', {})
    wk_schs = cmd_dict.get('WEEK-SCHEDULE-PD', {})
    annual_schs = cmd_dict.get('SCHEDULE-PD', {})

    # Get the DEFAULTS dicts for SPACE and ZONE
    space_defaults = defaults.get(('SPACE', ''), {})
    zone_defaults = defaults.get(('ZONE', 'CONDITIONED'), {})

    # Map zone name to parent system attrs for MIN-AIR-SCH lookup
    zone_to_system = {}
    for sys_name, sys_attrs in systems.items():
        sys_zones = child_objects_from_parent(
            cmd_dict, sys_name, 'SYSTEM', 'ZONE')
        sys_type = sys_attrs.get('TYPE', '').strip('"')
        sys_defaults = defaults.get(('SYSTEM', sys_type), {})
        for z_name in sys_zones:
            # Grabbing just MIN-AIR-SCH
            zone_to_system[z_name] = resolve_defaults(
                sys_attrs, sys_defaults, ('MIN-AIR-SCH',))
    
    # Map space to linked zone
    space_to_zone = {}
    space_to_zone_name = {}
    for z_name, z_attrs in zones.items():
        spc_ref = str(z_attrs.get('SPACE', '')).strip('"')
        if spc_ref:
            space_to_zone[spc_ref] = resolve_defaults(
                z_attrs, zone_defaults, ZONE_KEYS)
            space_to_zone_name[spc_ref] = z_name

    # Group spaces by C-ACTIVITY-DESC
    activity_groups = defaultdict(list)
    for spc_name, spc_attrs in spaces.items():
        activity = (str(spc_attrs.get('C-ACTIVITY-DESC', ''))
                    .replace('*', '')
                    .strip())
        if activity:
            activity_groups[activity].append((spc_name, spc_attrs))

    program_types = []
    for activity, spc_list in activity_groups.items():
        # use the first space as the program type attrs
        spc_name, spc_attrs = spc_list[0]

        # resolve defaults if any
        resolved_space = resolve_defaults(spc_attrs, space_defaults,
                                          SPACE_KEYS)

        # find the linked zone attrs
        resolved_zone = space_to_zone.get(spc_name)
        if resolved_zone is None:
            # No linked zone - apply defaults to empty dict
            resolved_zone = resolve_defaults({}, zone_defaults, ZONE_KEYS)

        # Get MIN-AIR-SCH from parent SYSTEM if available
        zone_name = space_to_zone_name.get(spc_name)
        parent_system = zone_to_system.get(zone_name, {}) if zone_name else {}

        # Add C-ACTIVITY-DESC from the space so switch solving works
        if 'C-ACTIVITY-DESC' not in resolved_zone:
            resolved_zone = dict(resolved_zone)
            resolved_zone['C-ACTIVITY-DESC'] = spc_attrs.get('C-ACTIVITY-DESC',
                                                             '')

        # Build schedule dict for any schedules referenced in the space/zone
        schedule_dict = build_schedule_dict(day_schs, wk_schs, annual_schs)

        # Resolve schedules for space loads
        people_sch = resolve_schedule(
            resolved_space.get('PEOPLE-SCHEDULE'), schedule_dict,
            lib_file_path)
        lighting_sch = resolve_schedule(
            resolved_space.get('LIGHTING-SCHEDULE') or
            resolved_space.get('LIGHTING-SCHEDUL'), schedule_dict,
            lib_file_path)
        equip_sch = resolve_schedule(
            resolved_space.get('EQUIP-SCHEDULE'), schedule_dict, lib_file_path)
        inf_sch = resolve_schedule(
            resolved_space.get('INF-SCHEDULE'), schedule_dict, lib_file_path)

        # Resolve zone level schedules
        heat_sch = resolve_schedule(
            resolved_zone.get('HEAT-TEMP-SCH'), schedule_dict, lib_file_path)
        cool_sch = resolve_schedule(
            resolved_zone.get('COOL-TEMP-SCH'), schedule_dict, lib_file_path)

        # Resolve MIN-AIR-SCH from parent SYSTEM
        min_air_sch_name = (
            parent_system.get('MIN-AIR-SCH') or
            resolved_zone.get('MIN-FLOW-SCH'))
        min_air_sch = resolve_schedule(
            min_air_sch_name, schedule_dict, lib_file_path)

        # Build Program Type loads with resolved schedules
        people = people_from_inp(resolved_space, people_sch)
        lighting = lighting_from_inp(resolved_space, lighting_sch)
        equipment = electric_equipment_from_inp(resolved_space, equip_sch)
        infiltration = infiltration_from_inp(resolved_space, inf_sch)
        setpoint = setpoint_from_inp(resolved_zone, heat_sch, cool_sch)
        ventilation = ventilation_from_inp(resolved_zone, min_air_sch)

        prog_id = clean_string(activity)
        prog = ProgramType(prog_id)
        prog.display_name = activity
        if people is not None:
            prog.people = people
        if lighting is not None:
            prog.lighting = lighting
        if equipment is not None:
            prog.electric_equipment = equipment
        if infiltration is not None:
            prog.infiltration = infiltration
        if setpoint is not None:
            prog.setpoint = setpoint
        if ventilation is not None:
            prog.ventilation = ventilation
        program_types.append(prog)

    return program_types


def switch_dict_to_space_inp(switch_dict):
    """Translate a switch statement dictionary into INP strings for the SPACE.

    Args:
        switch_dict: An dictionary with INP keywords as keys (such as
            PEOPLE-SCHEDULE or AREA/PERSON or LIGHTING-W/AREA). The values of the
            dictionary should be lists of switch statement text strings, such as
            'case "conf": #SI("Small Off Occ", "SPACE", "PEOPLE-SCHEDULE")'.

    Returns:
        A text string to be written into an INP file. This should go at the top
        of the description of Floors / Spaces.
    """
    # loop through the space keys and build a list of all switch statement keys
    all_switch_strs = []
    for s_key in SPACE_KEYS:
        try:
            if len(s_key) > 16:  # switch statements limit characters to 16
                s_key = s_key[:16]
            switch_progs = switch_dict[s_key]
            switch_strs = ['SET-DEFAULT FOR SPACE']
            switch_strs.append('   {} ='.format(s_key))
            switch_strs.append('{switch(#L("C-ACTIVITY-DESC"))')
            switch_strs.extend(switch_progs)
            switch_strs.append('default: no_default')
            switch_strs.append('endswitch}')
            switch_strs.append('..\n')
            all_switch_strs.append('\n'.join(switch_strs))
        except KeyError:
            pass  # none of the programs types have this space key
    # add something to set the INF-METHOD for all spaces
    inf_str = 'SET-DEFAULT FOR SPACE\n' \
        '   INF-METHOD = AIR-CHANGE\n' \
        '..\n'
    all_switch_strs.append(inf_str)
    return '\n'.join(all_switch_strs)


def switch_dict_to_zone_inp(switch_dict):
    """Translate a switch statement dictionary into INP strings for the ZONE.

    Args:
        switch_dict: An dictionary with INP keywords as keys (such as
            HEAT-TEMP-SCH or DESIGN-HEAT-T or OUTSIDE-AIR-FLOW). The values of the
            dictionary should be lists of switch statement text strings, such as
            'case "conf": #SI("Small Off HtgStp", "SPACE", "HEAT-TEMP-SCH")'.

    Returns:
        A text string to be written into an INP file. This should go at the top
        of the  description of HVAC Systems / Zones.
    """
    # loop through the space keys and build a list of all switch statement keys
    all_switch_strs = []
    for s_key in ZONE_KEYS:
        try:
            switch_progs = switch_dict[s_key]
            switch_strs = ['SET-DEFAULT FOR ZONE', '   TYPE = CONDITIONED']
            switch_strs.append('   {} ='.format(s_key))
            switch_strs.append('{switch(#LR("SPACE", "C-ACTIVITY-DESC"))')
            switch_strs.extend(switch_progs)
            switch_strs.append('default: no_default')
            switch_strs.append('endswitch}')
            switch_strs.append('..\n')
            all_switch_strs.append('\n'.join(switch_strs))
        except KeyError:
            pass  # none of the programs types have this space key
    return '\n'.join(all_switch_strs)
