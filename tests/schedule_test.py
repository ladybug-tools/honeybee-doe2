# coding=utf-8
from ladybug.dt import Time, Date
from honeybee_energy.schedule.day import ScheduleDay
from honeybee_energy.schedule.rule import ScheduleRule
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.schedule.fixedinterval import ScheduleFixedInterval
import honeybee_energy.lib.scheduletypelimits as schedule_types

from honeybee_doe2.schedule import schedule_day_to_inp, schedule_ruleset_to_inp, \
    schedule_fixed_interval_to_inp, schedule_day_from_inp, schedule_ruleset_from_inp

from tests.util_test import SCHEDULE_DAY_STR, SCHEDULE_DAY_PD_STR


def test_schedule_day_to_inp():
    """Test ScheduleDay to_inp."""
    simple_office = ScheduleDay('Simple Office Occupancy', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    inp_str = schedule_day_to_inp(simple_office)
    assert inp_str == \
        '"Simple Office Occupancy" = DAY-SCHEDULE\n' \
        '   TYPE                     = FRACTION\n' \
        '   HOURS                    = (1, 9)\n' \
        '   VALUES                   = (0.0)\n' \
        '   HOURS                    = (10, 17)\n' \
        '   VALUES                   = (1.0)\n' \
        '   HOURS                    = (18, 24)\n' \
        '   VALUES                   = (0.0)\n' \
        '   ..\n'
    rebuilt_sch = schedule_day_from_inp(inp_str)
    assert schedule_day_to_inp(rebuilt_sch) == inp_str

    simple_office2 = ScheduleDay(
        'Simple Office Occupancy', [1, 0.5, 1, 0.5, 1],
        [Time(0, 0), Time(6, 0), Time(12, 0), Time(16, 0), Time(20, 0)])
    inp_str = schedule_day_to_inp(simple_office2)
    assert inp_str == \
        '"Simple Office Occupancy" = DAY-SCHEDULE\n' \
        '   TYPE                     = FRACTION\n' \
        '   HOURS                    = (1, 6)\n' \
        '   VALUES                   = (1.0)\n' \
        '   HOURS                    = (7, 12)\n' \
        '   VALUES                   = (0.5)\n' \
        '   HOURS                    = (13, 16)\n' \
        '   VALUES                   = (1.0)\n' \
        '   HOURS                    = (17, 20)\n' \
        '   VALUES                   = (0.5)\n' \
        '   HOURS                    = (21, 24)\n' \
        '   VALUES                   = (1.0)\n' \
        '   ..\n'
    rebuilt_sch = schedule_day_from_inp(inp_str)
    assert schedule_day_to_inp(rebuilt_sch) == inp_str

    equest_sample = [0, 0, 0, 0, 0, 0, 0, 0, 0.3,0.6,0.8,
                     1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]
    equest_sample_sch = ScheduleDay.from_values_at_timestep(
        'eQuest Sample Sch Day', equest_sample)
    inp_str = schedule_day_to_inp(equest_sample_sch)
    assert inp_str == \
        '"eQuest Sample Sch Day" = DAY-SCHEDULE\n' \
        '   TYPE                     = FRACTION\n' \
        '   HOURS                    = (1, 8)\n' \
        '   VALUES                   = (0.0)\n' \
        '   HOURS                    = (9, 11)\n' \
        '   VALUES                   = (0.3, 0.6, 0.8)\n' \
        '   HOURS                    = (12, 18)\n' \
        '   VALUES                   = (1.0)\n' \
        '   HOURS                    = (19, 24)\n' \
        '   VALUES                   = (0.0)\n' \
        '   ..\n'
    rebuilt_sch = schedule_day_from_inp(inp_str)
    assert schedule_day_to_inp(rebuilt_sch) == inp_str


def test_schedule_day_to_inp_start_end_change():
    """Test ScheduleDay to_inp with values that change in the first and last hour."""
    hourly_vals_from_ep = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.166, 0.33, 0.5,
                           0.66, 0.833, 1.0, 0.75, 0.5, 0.25, 0.0, 0.25, 0.5,
                           0.75, 1.0, 0.75, 0.5, 0.25, 0.0]
    complex_office = ScheduleDay.from_values_at_timestep(
        'Complex Office Occupancy', hourly_vals_from_ep)
    inp_str = schedule_day_to_inp(complex_office)
    assert inp_str == \
        '"Complex Office Occupancy" = DAY-SCHEDULE\n' \
        '   TYPE                     = FRACTION\n' \
        '   HOURS                    = (1, 6)\n' \
        '   VALUES                   = (0.0)\n' \
        '   HOURS                    = (7, 24)\n' \
        '   VALUES                   = (0.166, 0.33, 0.5, 0.66, 0.833,\n' \
        '                               1.0, 0.75, 0.5, 0.25, 0.0,\n' \
        '                               0.25, 0.5, 0.75, 1.0, 0.75,\n' \
        '                               0.5, 0.25, 0.0)\n' \
        '   ..\n'
    rebuilt_sch = schedule_day_from_inp(inp_str)
    assert schedule_day_to_inp(rebuilt_sch) == inp_str

    hourly_vals_from_ep[-2] = 0
    complex_office = ScheduleDay.from_values_at_timestep(
        'Complex Office Occupancy', hourly_vals_from_ep)
    inp_str = schedule_day_to_inp(complex_office)
    assert inp_str == \
        '"Complex Office Occupancy" = DAY-SCHEDULE\n' \
        '   TYPE                     = FRACTION\n' \
        '   HOURS                    = (1, 6)\n' \
        '   VALUES                   = (0.0)\n' \
        '   HOURS                    = (7, 22)\n' \
        '   VALUES                   = (0.166, 0.33, 0.5, 0.66, 0.833,\n' \
        '                               1.0, 0.75, 0.5, 0.25, 0.0,\n' \
        '                               0.25, 0.5, 0.75, 1.0, 0.75,\n' \
        '                               0.5)\n' \
        '   HOURS                    = (23, 24)\n' \
        '   VALUES                   = (0.0)\n' \
        '   ..\n'
    rebuilt_sch = schedule_day_from_inp(inp_str)
    assert schedule_day_to_inp(rebuilt_sch) == inp_str

    hourly_vals_from_ep[1] = 1.0
    complex_office = ScheduleDay.from_values_at_timestep(
        'Complex Office Occupancy', hourly_vals_from_ep)
    inp_str = schedule_day_to_inp(complex_office)
    assert inp_str == \
        '"Complex Office Occupancy" = DAY-SCHEDULE\n' \
        '   TYPE                     = FRACTION\n' \
        '   HOURS                    = (1, 2)\n' \
        '   VALUES                   = (0.0, 1.0)\n' \
        '   HOURS                    = (3, 6)\n' \
        '   VALUES                   = (0.0)\n' \
        '   HOURS                    = (7, 22)\n' \
        '   VALUES                   = (0.166, 0.33, 0.5, 0.66, 0.833,\n' \
        '                               1.0, 0.75, 0.5, 0.25, 0.0,\n' \
        '                               0.25, 0.5, 0.75, 1.0, 0.75,\n' \
        '                               0.5)\n' \
        '   HOURS                    = (23, 24)\n' \
        '   VALUES                   = (0.0)\n' \
        '   ..\n'
    rebuilt_sch = schedule_day_from_inp(inp_str)
    assert schedule_day_to_inp(rebuilt_sch) == inp_str
    
    hourly_vals_from_ep[0] = 1.0
    hourly_vals_from_ep[1] = 0.0
    complex_office = ScheduleDay.from_values_at_timestep(
        'Complex Office Occupancy', hourly_vals_from_ep)
    inp_str = schedule_day_to_inp(complex_office)
    assert inp_str == \
        '"Complex Office Occupancy" = DAY-SCHEDULE\n' \
        '   TYPE                     = FRACTION\n' \
        '   HOURS                    = (1, 2)\n' \
        '   VALUES                   = (1.0, 0.0)\n' \
        '   HOURS                    = (3, 6)\n' \
        '   VALUES                   = (0.0)\n' \
        '   HOURS                    = (7, 22)\n' \
        '   VALUES                   = (0.166, 0.33, 0.5, 0.66, 0.833,\n' \
        '                               1.0, 0.75, 0.5, 0.25, 0.0,\n' \
        '                               0.25, 0.5, 0.75, 1.0, 0.75,\n' \
        '                               0.5)\n' \
        '   HOURS                    = (23, 24)\n' \
        '   VALUES                   = (0.0)\n' \
        '   ..\n'
    rebuilt_sch = schedule_day_from_inp(inp_str)
    assert schedule_day_to_inp(rebuilt_sch) == inp_str


def test_schedule_ruleset_to_inp():
    """Test the ScheduleRuleset to_inp method."""
    weekday_office = ScheduleDay('Weekday Office Occupancy', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Occupancy', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    sunday_office = ScheduleDay('Sunday Office Occupancy', [0])
    sat_rule = ScheduleRule(saturday_office, apply_saturday=True)
    sun_rule = ScheduleRule(sunday_office, apply_sunday=True)
    summer_office = ScheduleDay('Summer Office Occupancy', [0, 1, 0.25],
                                [Time(0, 0), Time(6, 0), Time(22, 0)])
    winter_office = ScheduleDay('Winter Office Occupancy', [0])
    schedule = ScheduleRuleset('Office Occupancy', weekday_office,
                               [sat_rule, sun_rule], schedule_types.fractional,
                               sunday_office, summer_office, winter_office)

    inp_yr_str, inp_week_strs = schedule_ruleset_to_inp(schedule)

    assert inp_yr_str == \
        '"Office Occupancy" = SCHEDULE\n' \
        '   TYPE                     = FRACTION\n' \
        '   THRU DEC 31              = "Office Occupancy Week 1"\n' \
        '   ..\n'
    assert len(inp_week_strs) == 1
    assert inp_week_strs[0] == \
        '"Office Occupancy Week 1" = WEEK-SCHEDULE-PD\n' \
        '   TYPE                     = FRACTION\n' \
        '   DAY-SCHEDULES            = (\n' \
        '      "Weekday Office Occupancy", $ Monday,\n' \
        '      "Weekday Office Occupancy", $ Tuesday,\n' \
        '      "Weekday Office Occupancy", $ Wednesday,\n' \
        '      "Weekday Office Occupancy", $ Thursday,\n' \
        '      "Weekday Office Occupancy", $ Friday,\n' \
        '      "Saturday Office Occupancy", $ Saturday,\n' \
        '      "Sunday Office Occupancy", $ Sunday,\n' \
        '      "Sunday Office Occupancy", $ Holiday,\n' \
        '      "Winter Office Occupancy", $ Winter Design Day,\n' \
        '      "Summer Office Occupancy", $ Summer Design Day,\n' \
        '   )\n' \
        '   ..\n'
    
    day_sch_strs = [schedule_day_to_inp(day_sch)
                    for day_sch in schedule.day_schedules]
    rebuilt_sch = schedule_ruleset_from_inp(inp_yr_str, inp_week_strs, day_sch_strs)
    assert isinstance(rebuilt_sch, ScheduleRuleset)
    inp_yr_str, inp_week_strs = schedule_ruleset_to_inp(rebuilt_sch)
    assert len(inp_week_strs) == 1


def test_schedule_ruleset_to_inp_date_range():
    """Test the ScheduleRuleset to_inp method with schedules over a date range."""
    weekday_school = ScheduleDay('Weekday School Year', [0.1, 1, 0.1],
                                 [Time(0, 0), Time(8, 0), Time(17, 0)])
    weekend_school = ScheduleDay('Weekend School Year', [0.1])
    weekday_summer = ScheduleDay('Weekday Summer', [0, 0.5, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_summer = ScheduleDay('Weekend Summer', [0])

    summer_weekday_rule = ScheduleRule(
        weekday_summer, start_date=Date(7, 1), end_date=Date(9, 1))
    summer_weekday_rule.apply_weekday = True
    summer_weekend_rule = ScheduleRule(
        weekend_summer, start_date=Date(7, 1), end_date=Date(9, 1))
    summer_weekend_rule.apply_weekend = True
    school_weekend_rule = ScheduleRule(weekend_school)
    school_weekend_rule.apply_weekend = True

    summer_design = ScheduleDay('School Summer Design', [0, 1, 0.25],
                                [Time(0, 0), Time(6, 0), Time(18, 0)])
    winter_design = ScheduleDay('School Winter Design', [0])

    all_rules = [summer_weekday_rule, summer_weekend_rule, school_weekend_rule]
    school_schedule = ScheduleRuleset(
        'School Occupancy', weekday_school, all_rules, schedule_types.fractional,
        None, summer_design, winter_design)

    inp_yr_str, inp_week_strs = schedule_ruleset_to_inp(school_schedule)

    assert inp_yr_str == \
        '"School Occupancy" = SCHEDULE\n' \
        '   TYPE                     = FRACTION\n' \
        '   THRU JUN 30              = "School Occupancy Week 1"\n' \
        '   THRU SEP 1               = "School Occupancy Week 2"\n' \
        '   THRU DEC 31              = "School Occupancy Week 1"\n' \
        '   ..\n' \
        or inp_yr_str == \
        '"School Occupancy" = SCHEDULE\n' \
        '   TYPE                     = FRACTION\n' \
        '   THRU JUN 30              = "School Occupancy Week 2"\n' \
        '   THRU SEP 1               = "School Occupancy Week 1"\n' \
        '   THRU DEC 31              = "School Occupancy Week 2"\n' \
        '   ..\n'
    assert len(inp_week_strs) == 2

    day_sch_strs = [schedule_day_to_inp(day_sch)
                    for day_sch in school_schedule.day_schedules]
    rebuilt_sch = schedule_ruleset_from_inp(inp_yr_str, inp_week_strs, day_sch_strs)
    assert isinstance(rebuilt_sch, ScheduleRuleset)
    inp_yr_str, inp_week_strs = schedule_ruleset_to_inp(rebuilt_sch)
    assert len(inp_week_strs) >= 2


def test_schedule_fixedinterval_to_inp():
    """Test the ScheduleFixedInterval to_inp method."""
    trans_sched = ScheduleFixedInterval(
        'Custom Transmittance', [x / 8760 for x in range(8760)],
        schedule_types.fractional)
    inp_yr_str, inp_week_strs, inp_day_strs = schedule_fixed_interval_to_inp(trans_sched)

    assert inp_yr_str == \
        '"Custom Transmittance" = SCHEDULE\n' \
        '   TYPE                     = FRACTION\n' \
        '   THRU JAN 31              = "Custom TransmittanceJan"\n' \
        '   THRU FEB 28              = "Custom TransmittanceFeb"\n' \
        '   THRU MAR 31              = "Custom TransmittanceMar"\n' \
        '   THRU APR 30              = "Custom TransmittanceApr"\n' \
        '   THRU MAY 31              = "Custom TransmittanceMay"\n' \
        '   THRU JUN 30              = "Custom TransmittanceJun"\n' \
        '   THRU JUL 31              = "Custom TransmittanceJul"\n' \
        '   THRU AUG 31              = "Custom TransmittanceAug"\n' \
        '   THRU SEP 30              = "Custom TransmittanceSep"\n' \
        '   THRU OCT 31              = "Custom TransmittanceOct"\n' \
        '   THRU NOV 30              = "Custom TransmittanceNov"\n' \
        '   THRU DEC 31              = "Custom TransmittanceDec"\n' \
        '   ..\n'

    assert len(inp_week_strs) == 12
    assert inp_week_strs[0] == \
        '"Custom TransmittanceJan" = WEEK-SCHEDULE\n' \
        '   TYPE                     = FRACTION\n' \
        '   DAYS                     = (ALL)\n' \
        '   DAY-SCHEDULES            = ("Custom TransmittanceJanDay")\n' \
        '   ..\n'

    assert len(inp_day_strs) == 12
    assert inp_day_strs[0] == \
        '"Custom TransmittanceJanDay" = DAY-SCHEDULE-PD\n' \
        '   TYPE                     = FRACTION\n' \
        '   VALUES                   = (\n' \
        '      0.041,\n' \
        '      0.041,\n' \
        '      0.041,\n' \
        '      0.041,\n' \
        '      0.042,\n' \
        '      0.042,\n' \
        '      0.042,\n' \
        '      0.042,\n' \
        '      0.042,\n' \
        '      0.042,\n' \
        '      0.042,\n' \
        '      0.042,\n' \
        '      0.042,\n' \
        '      0.043,\n' \
        '      0.043,\n' \
        '      0.043,\n' \
        '      0.043,\n' \
        '      0.043,\n' \
        '      0.043,\n' \
        '      0.043,\n' \
        '      0.043,\n' \
        '      0.043,\n' \
        '      0.044,\n' \
        '      0.044,\n' \
        '   )\n' \
        '   ..\n'


def test_schedule_day_from_inp():
    """Test ScheduleDay from_inp."""
    schedule_day = schedule_day_from_inp(SCHEDULE_DAY_STR)
    assert schedule_day.identifier == 'College HTGSETP SCH Wkdy'
    assert schedule_day.values == (15.56, 17.78, 20.0, 21.11, 15.56)
    assert tuple(str(t) for t in schedule_day.times) == \
        ('00:00', '06:00', '07:00', '08:00', '21:00')
    
    schedule_day = schedule_day_from_inp(SCHEDULE_DAY_PD_STR)
    assert schedule_day.identifier == 'PRJ Heating SAT'
    assert schedule_day.values == (18.33, 19.17, 20.0, 21.11, 18.33)
    assert tuple(str(t) for t in schedule_day.times) == \
        ('00:00', '06:00', '07:00', '08:00', '16:00')
