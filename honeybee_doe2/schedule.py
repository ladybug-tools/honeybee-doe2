# coding=utf-8
"""honeybee-doe2 schedule translators."""
from ladybug.dt import Date, MONTHNAMES
from honeybee.typing import clean_doe2_string

from .config import RES_CHARS
from .util import generate_inp_string


def schedule_type_limit_to_inp(type_limit):
    """Get the DOE-2 type for a honeybee-energy ScheduleTypeLimit."""
    if type_limit is None:
        return 'FRACTION'
    elif type_limit.unit_type == 'Temperature':
        return 'TEMPERATURE'
    else:
        if type_limit.numeric_type == 'Discrete':
            return 'ON/OFF'
        else:
            return 'FRACTION'


def schedule_day_to_inp(day_schedule, type_limit=None):
    """Convert a ScheduleDay into a DAY-SCHEDULE INP string."""
    # setup the DOE-2 identifier and lists for keywords and values
    doe2_id = clean_doe2_string(day_schedule.identifier, RES_CHARS)
    type_text = schedule_type_limit_to_inp(type_limit)
    keywords, values = ['TYPE'], [type_text]
    hour_values = day_schedule.values_at_timestep(1)

    # setup a function to format list of values correctly
    def _format_day_values(values_to_format):
        if len(values_to_format) == 1:
            return'({})'.format(values_to_format[0])
        else:
            return str(tuple(values_to_format))

    # loop through the hourly values and write them in the format DOE-2 likes
    prev_count, prev_hour, prev_values = 0, 1, [hour_values[0]]
    for i, val in enumerate(hour_values):
        if i == 0:
            continue  # ignore the first value already in the list
        if val == prev_values[-1]:
            prev_count += 1
            if len(prev_values) > 1:
                keywords.append('HOURS')
                if prev_hour != i - 1:
                    values.append('({}, {})'.format(prev_hour, i - 1))
                    keywords.append('VALUES')
                    values.append(_format_day_values(prev_values[:-1]))
                    prev_values = [prev_values[-1]]
                    prev_hour = i
                else:
                    values.append('({}, {})'.format(prev_hour, i))
                    keywords.append('VALUES')
                    values.append(_format_day_values(prev_values))
                    prev_values = [prev_values[-1]]
                    prev_hour = i + 1
            continue  # wait for the value to change
        if prev_count == 0:  # just keep assembling the list of values
            prev_values.append(val)
        else:
            keywords.append('HOURS')
            values.append('({}, {})'.format(prev_hour, i))
            keywords.append('VALUES')
            values.append(_format_day_values(prev_values))
            prev_values = [val]
            prev_hour = i + 1
        prev_count = 0
    keywords.append('HOURS')
    values.append('({}, {})'.format(prev_hour, 24))
    keywords.append('VALUES')
    values.append(_format_day_values(prev_values))

    # return the INP string
    return generate_inp_string(doe2_id, 'DAY-SCHEDULE', keywords, values)


def schedule_ruleset_to_inp(schedule):
    """Convert a ScheduleRuleset into a WEEK-SCHEDULE and SCHEDULE INP strings.
    
    Note that this method only outputs SCHEDULE and WEEK-SCHEDULE objects
    However, to write the full schedule into an INP, the schedules's
    day_schedules must also be written.

    Returns:
        A tuple with two elements

        -   year_schedule: Text string representation of the SCHEDULE
            describing this schedule.

        -   week_schedules: A list of WEEK-SCHEDULE test strings that are
            referenced in the year_schedule.
    """
    # setup the DOE-2 identifier and lists for keywords and values
    doe2_id = clean_doe2_string(schedule.identifier, RES_CHARS)
    type_text = schedule_type_limit_to_inp(schedule.schedule_type_limit)
    day_types = ['(MON)', '(TUE)', '(WED)', '(THU)', '(FRI)', '(SAT)', '(SUN)',
                 '(HOL)', '(HDD)', '(CDD)']

    def _get_week_list(schedule, rule_indices):
        """Get a list of the ScheduleDay identifiers applied on each day of the week."""
        week_list = []
        for dow in range(7):
            for i in rule_indices:
                if schedule._schedule_rules[i].week_apply_tuple[dow]:
                    day_sch_id = schedule._schedule_rules[i].schedule_day.identifier
                    week_list.append(clean_doe2_string(day_sch_id, RES_CHARS))
                    break
            else:  # no rule applies; use default_day_schedule.
                day_sch_id = schedule.default_day_schedule.identifier
                week_list.append(clean_doe2_string(day_sch_id, RES_CHARS))
        week_list.append(week_list.pop(0))  # DOE-2 starts week on Monday; not Sunday
        return week_list

    def _get_extra_week_fields(schedule):
        """Get schedule identifiers of extra days in Schedule:Week."""
        # add summer and winter design days
        week_fields = []
        if schedule._holiday_schedule is not None:
            day_sch_id = schedule._holiday_schedule.identifier
            week_fields.append(clean_doe2_string(day_sch_id, RES_CHARS))
        else:
            day_sch_id = schedule._default_day_schedule.identifier
            week_fields.append(clean_doe2_string(day_sch_id, RES_CHARS))
        if schedule._winter_designday_schedule is not None:
            day_sch_id = schedule._winter_designday_schedule.identifier
            week_fields.append(clean_doe2_string(day_sch_id, RES_CHARS))
        else:
            day_sch_id = schedule._default_day_schedule.identifier
            week_fields.append(clean_doe2_string(day_sch_id, RES_CHARS))
        if schedule._summer_designday_schedule is not None:
            day_sch_id = schedule._summer_designday_schedule.identifier
            week_fields.append(clean_doe2_string(day_sch_id, RES_CHARS))
        else:
            day_sch_id = schedule._default_day_schedule.identifier
            week_fields.append(clean_doe2_string(day_sch_id, RES_CHARS))
        return week_fields

    def _inp_week_schedule_from_rule_indices(schedule, rule_indices, week_index):
        """Create an INP string of a week schedule from a list of rules indices."""
        week_sch_id = '{}_Week {}'.format(schedule.identifier, week_index)
        week_sch_id = clean_doe2_string(week_sch_id, RES_CHARS)
        week_fields = []
        # check rules that apply for the days of the week
        week_fields.extend(_get_week_list(schedule, rule_indices))
        # add extra days (including summer and winter design days)
        week_fields.extend(_get_extra_week_fields(schedule))
        week_keywords, week_values = ['TYPE'], [type_text]
        for day_type, day_sch in zip(day_types, week_fields):
            week_keywords.append('DAYS')
            week_values.append(day_type)
            week_keywords.append('DAY-SCHEDULES')
            week_values.append('"{}"'.format(day_sch))
        week_schedule = generate_inp_string(
            week_sch_id, 'WEEK-SCHEDULE', week_keywords, week_values)
        return week_schedule, week_sch_id

    def _inp_week_schedule_from_week_list(schedule, week_list, week_index):
        """Create an INP string of a week schedule from a list ScheduleDay identifiers.
        """
        week_sch_id = '{}_Week {}'.format(schedule.identifier, week_index)
        week_sch_id = clean_doe2_string(week_sch_id, RES_CHARS)
        week_fields = list(week_list)
        week_fields.append(week_fields.pop(0))  # DOE-2 starts week on Monday; not Sunday
        week_fields.extend(_get_extra_week_fields(schedule))
        week_keywords, week_values = ['TYPE'], [type_text]
        for day_type, day_sch in zip(day_types, week_fields):
            week_keywords.append('DAYS')
            week_values.append(day_type)
            week_keywords.append('DAY-SCHEDULES')
            week_values.append('"{}"'.format(day_sch))
        week_schedule = generate_inp_string(
            week_sch_id, 'WEEK-SCHEDULE', week_keywords, week_values)
        return week_schedule, week_sch_id

    # prepare to create a full Schedule:Year
    week_schedules = []
    if schedule.is_single_week:  # create the only one week schedule
        wk_sch, wk_sch_id = \
            _inp_week_schedule_from_rule_indices(schedule, range(len(schedule)), 1)
        week_schedules.append(wk_sch)
        yr_wk_s_ids = [wk_sch_id]
        yr_wk_dt_range = [[Date(1, 1), Date(12, 31)]]
    else:  # create a set of week schedules throughout the year
        # loop through 365 days of the year to find unique combinations of rules
        rules_each_day = []
        for doy in range(1, 366):
            rules_on_doy = tuple(i for i, rule in enumerate(schedule._schedule_rules)
                                 if rule.does_rule_apply_doy(doy))
            rules_each_day.append(rules_on_doy)
        unique_rule_sets = set(rules_each_day)
        # check if any combination yield the same week schedule and remove duplicates
        week_tuples = [tuple(_get_week_list(schedule, rule_set))
                       for rule_set in unique_rule_sets]
        unique_week_tuples = list(set(week_tuples))
        # create the unique week schedules from the combinations of rules
        week_sched_ids = []
        for i, week_list in enumerate(unique_week_tuples):
            wk_schedule, wk_sch_id = \
                _inp_week_schedule_from_week_list(schedule, week_list, i + 1)
            week_schedules.append(wk_schedule)
            week_sched_ids.append(wk_sch_id)
        # create a dictionary mapping unique rule index lists to week schedule ids
        rule_set_map = {}
        for rule_i, week_list in zip(unique_rule_sets, week_tuples):
            unique_week_i = unique_week_tuples.index(week_list)
            rule_set_map[rule_i] = week_sched_ids[unique_week_i]
        # loop through all 365 days of the year to find when rules change
        yr_wk_s_ids = []
        yr_wk_dt_range = []
        prev_week_sched = None
        for doy in range(1, 366):
            week_sched = rule_set_map[rules_each_day[doy - 1]]
            if week_sched != prev_week_sched:  # change to a new rule set
                yr_wk_s_ids.append(week_sched)
                if doy != 1:
                    yr_wk_dt_range[-1].append(Date.from_doy(doy - 1))
                    yr_wk_dt_range.append([Date.from_doy(doy)])
                else:
                    yr_wk_dt_range.append([Date(1, 1)])
                prev_week_sched = week_sched
        yr_wk_dt_range[-1].append(Date(12, 31))

    # create the year fields
    keywords, values = ['TYPE'], [type_text]
    for i, (wk_sch_id, dt_range) in enumerate(zip(yr_wk_s_ids, yr_wk_dt_range)):
        end_date = dt_range[1]
        thru = 'THRU {} {}'.format(MONTHNAMES[end_date.month - 1].upper(), end_date.day)
        keywords.append(thru)
        values.append('"{}"'.format(wk_sch_id))
    year_schedule = generate_inp_string(doe2_id, 'SCHEDULE', keywords, values)
    return year_schedule, week_schedules


def energy_trans_sch_to_transmittance(shade_obj):
    """Try to extract the transmittance from the shade energy properties."""
    trans = 0
    trans_sch = shade_obj.properties.energy.transmittance_schedule
    if trans_sch is not None:
        if trans_sch.is_constant:
            try:  # assume ScheduleRuleset
                trans = trans_sch.default_day_schedule[0]
            except AttributeError:  # ScheduleFixedInterval
                trans = trans_sch.values[0]
        else:  # not a constant schedule; use the average transmittance
            try:  # assume ScheduleRuleset
                sch_vals = trans_sch.values()
            except Exception:  # ScheduleFixedInterval
                sch_vals = trans_sch.values
            trans = sum(sch_vals) / len(sch_vals)
    return trans
