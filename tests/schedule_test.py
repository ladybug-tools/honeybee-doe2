# coding=utf-8
from ladybug.dt import Time, Date
from honeybee_energy.schedule.day import ScheduleDay
from honeybee_energy.schedule.rule import ScheduleRule
from honeybee_energy.schedule.ruleset import ScheduleRuleset
import honeybee_energy.lib.scheduletypelimits as schedule_types

from honeybee_doe2.schedule import schedule_day_to_inp, schedule_ruleset_to_inp


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

    print(inp_yr_str)
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
