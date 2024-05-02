# coding=utf-8
"""honeybee-doe2 schedule translators."""
from __future__ import division

from ladybug.dt import Date, MONTHNAMES
from ladybug.analysisperiod import AnalysisPeriod
from honeybee.typing import clean_doe2_string

from .config import RES_CHARS
from .util import generate_inp_string, generate_inp_string_list_format


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

    # convert temperature to fahrenheit if the type if temperature
    if type_text == 'TEMPERATURE':
        hour_values = [round(v * (9. / 5.) + 32., 2) for v in hour_values]

    # setup a function to format list of values correctly
    def _format_day_values(values_to_format):
        if len(values_to_format) == 1:
            return'({})'.format(round(values_to_format[0], 3))
        elif len(values_to_format) < 5:
            return str(tuple(round(v, 3) for v in values_to_format))
        else:  # we have to format it with multiple lines
            spc = ' ' * 31
            full_str = '('
            for i, v in enumerate(values_to_format):
                if i == len(values_to_format) - 1:
                    full_str += str(round(v, 3)) + ')'
                elif (i + 1) % 5 == 0:
                    full_str += str(round(v, 3)) + ',\n' + spc
                else:
                    full_str += str(round(v, 3)) + ', '
            return full_str

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
    """Convert a ScheduleRuleset into a WEEK-SCHEDULE-PD and SCHEDULE INP strings.
    
    Note that this method only outputs SCHEDULE and WEEK-SCHEDULE objects
    However, to write the full schedule into an INP, the schedules's
    day_schedules must also be written.

    Returns:
        A tuple with two elements

        -   year_schedule: Text string representation of the SCHEDULE
            describing this schedule.

        -   week_schedules: A list of WEEK-SCHEDULE-PD text strings that are
            referenced in the year_schedule.
    """
    # setup the DOE-2 identifier and lists for keywords and values
    doe2_id = clean_doe2_string(schedule.identifier, RES_CHARS)
    type_text = schedule_type_limit_to_inp(schedule.schedule_type_limit)
    day_types = [
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
        'Sunday', 'Holiday', 'Winter Design Day', 'Summer Design Day'
    ]

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
        day_list = []
        for day_type, day_sch in zip(day_types, week_fields):
            day_list.append('"{}", $ {}'.format(day_sch, day_type))
        week_keywords.append('DAY-SCHEDULES')
        week_values.append(day_list)
        week_schedule = generate_inp_string_list_format(
            week_sch_id, 'WEEK-SCHEDULE-PD', week_keywords, week_values)
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
        day_list = []
        for day_type, day_sch in zip(day_types, week_fields):
            day_list.append('"{}", $ {}'.format(day_sch, day_type))
        week_keywords.append('DAY-SCHEDULES')
        week_values.append(day_list)
        week_schedule = generate_inp_string_list_format(
            week_sch_id, 'WEEK-SCHEDULE-PD', week_keywords, week_values)
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


def schedule_fixed_interval_to_inp(schedule):
    """Convert a ScheduleFixedInterval to INP strings.

    Note that true Fixed Interval schedules are not supported by DOE-2 and there
    is no way to faithfully translate them given that DOE-2 SCHEDULE objects have
    a hard limit of 12 THRU statements. This method tries to write as best of
    an approximation for the schedule as possible by averaging the hourly values
    from each day of the fixed interval schedule. A separate day schedule will
    be used for each month in an attempt to account for changes in the fixed
    interval schedule over the year.

    All of this will allow the translation to succeed and gives roughly matching
    behavior of the DOE-2 simulation to the EnergyPlus simulation. However, it is
    recommended that users replace ScheduleFixedIntervals with ScheduleRulesets
    that they know best represents the schedule. Or EnergyPlus should be used for
    the simulation instead of DOE-2.

    Returns:
        A tuple with two elements

        -   year_schedule: Text string representation of the SCHEDULE
            describing this schedule.

        -   week_schedules: A list of WEEK-SCHEDULE text strings that are
            referenced in the year_schedule.
        
        -   day_schedules: A list of DAY-SCHEDULE-PD text strings that are
            referenced in the week_schedules.
    """
    # setup the DOE-2 identifier and lists for keywords and values
    doe2_id = clean_doe2_string(schedule.identifier, RES_CHARS)
    base_id = clean_doe2_string(schedule.identifier, RES_CHARS - 6)
    type_text = schedule_type_limit_to_inp(schedule.schedule_type_limit)

    # loop through the months of the year and create appropriate schedules
    day_schedules, week_schedules = [], []
    year_keywords, year_values = ['TYPE'], [type_text]
    sch_data = schedule.data_collection
    if sch_data.header.analysis_period.timestep != 1:
        sch_data = sch_data.cull_to_timestep(1)
    for month_i in range(1, 13):
        # create the day schedules
        month_name = AnalysisPeriod.MONTHNAMES[month_i]
        month_days = AnalysisPeriod.NUMOFDAYSEACHMONTH[month_i - 1]
        week_id = '{}{}'.format(base_id, month_name)
        day_id = '{}{}'.format(week_id, 'Day')
        period = AnalysisPeriod(st_month=month_i, end_month=month_i, end_day=month_days)
        month_data = sch_data.filter_by_analysis_period(period)
        mon_per_hr = month_data.average_monthly_per_hour()
        hour_values = [round(v, 3) for v in mon_per_hr.values]
        if type_text == 'TEMPERATURE':
            hour_values = [round(v * (9. / 5.) + 32., 2) for v in hour_values]
        day_keywords, day_values = ['TYPE', 'VALUES'], [type_text, hour_values]
        day_inp_str = generate_inp_string_list_format(
            day_id, 'DAY-SCHEDULE-PD', day_keywords, day_values)
        day_schedules.append(day_inp_str)
        # create week schedule
        week_keywords = ['TYPE', 'DAYS', 'DAY-SCHEDULES']
        week_values = [type_text, '(ALL)', '("{}")'.format(day_id)]
        week_sch = generate_inp_string(
            week_id, 'WEEK-SCHEDULE', week_keywords, week_values)
        week_schedules.append(week_sch)
        # add values to the year schedules
        thru = 'THRU {} {}'.format(month_name.upper(), period.end_day)
        year_keywords.append(thru)
        year_values.append('"{}"'.format(week_id))

    # return all of the strings
    year_schedule = generate_inp_string(doe2_id, 'SCHEDULE', year_keywords, year_values)
    return year_schedule, week_schedules, day_schedules


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
            trans = round(sum(sch_vals) / len(sch_vals), 3)
    return trans
