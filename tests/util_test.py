"""Test the utility functions."""
import os

from honeybee_doe2.util import parse_inp_string, parse_inp_file



SCHEDULE_DAY_STR = """
"College HTGSETP SCH Wkdy" = DAY-SCHEDULE
   TYPE                     = TEMPERATURE
   HOURS                    = (1, 6)
   VALUES                   = (60.0)
   HOURS                    = (7, 8)
   VALUES                   = (64.0, 68.0)
   HOURS                    = (9, 21)
   VALUES                   = (70.0)
   HOURS                    = (22, 24)
   VALUES                   = (60.0)
   ..
"""

SCHEDULE_DAY_PD_STR = """
"PRJ Heating SAT" = DAY-SCHEDULE-PD
   TYPE             = TEMPERATURE
   VALUES           = ( 65, &D, &D, &D, &D, &D, 66.5, 68, 70, &D, &D, &D, &D, 
         &D, &D, &D, 65 )
   ..
"""

SCHEDULE_WEEK_PD_STR = """
"College HTGSETP SCH Week 1" = WEEK-SCHEDULE-PD
   TYPE                     = TEMPERATURE
   DAY-SCHEDULES            = (
      "College HTGSETP SCH Wkdy", $ Monday,
      "College HTGSETP SCH Wkdy", $ Tuesday,
      "College HTGSETP SCH Wkdy", $ Wednesday,
      "College HTGSETP SCH Wkdy", $ Thursday,
      "College HTGSETP SCH Wkdy", $ Friday,
      "College HTGSETP SCH Wknd", $ Saturday,
      "College HTGSETP SCH Wknd", $ Sunday,
      "College HTGSETP SCH Hol", $ Holiday,
      "College HTGSETP SCH WntrDsn", $ Winter Design Day,
      "College HTGSETP SCH SmrDsn", $ Summer Design Day,
   )
   ..
"""

SCHEDULE_WEEK_PD_STR2 = """
"PRJ Heating Wk" = WEEK-SCHEDULE-PD
   TYPE             = TEMPERATURE
   DAY-SCHEDULES    = ( "PRJ Heating WD", &D, &D, &D, &D, "PRJ Heating SAT", 
         "PRJ Heating SUN, HOL" )
   ..
"""

SCHEDULE_YEAR_STR = """
"College HTGSETP SCH" = SCHEDULE
   TYPE                     = TEMPERATURE
   THRU DEC 31              = "College HTGSETP SCH Week 1"
   ..
"""

SCHEDULE_YEAR_PD_STR = """
"PRJ Heating Sch" = SCHEDULE-PD
   TYPE             = TEMPERATURE
   MONTH            = ( 12 )
   DAY              = ( 31 )
   WEEK-SCHEDULES   = ( "PRJ Heating Wk" )
   ..
"""


def test_parse_schedule_day():
    """Test the parsing of DAY-SCHEDULE."""
    u_name, command, keywords, values = parse_inp_string(SCHEDULE_DAY_STR)

    assert u_name == 'College HTGSETP SCH Wkdy'
    assert command == 'DAY-SCHEDULE'
    assert len(keywords) == 9
    assert len(values) == 9
    assert keywords[0] == 'TYPE'
    assert values[0] == 'TEMPERATURE'


def test_parse_schedule_day_pd():
    """Test the parsing of DAY-SCHEDULE-PD."""
    u_name, command, keywords, values = parse_inp_string(SCHEDULE_DAY_PD_STR)

    assert u_name == 'PRJ Heating SAT'
    assert command == 'DAY-SCHEDULE-PD'
    assert len(keywords) == 2
    assert len(values) == 2
    assert keywords[0] == 'TYPE'
    assert values[0] == 'TEMPERATURE'


def test_parse_schedule_week_pd():
    """Test the parsing of WEEK-SCHEDULE-PD."""
    u_name, command, keywords, values = parse_inp_string(SCHEDULE_WEEK_PD_STR)

    assert u_name == 'College HTGSETP SCH Week 1'
    assert command == 'WEEK-SCHEDULE-PD'
    assert len(keywords) == 2
    assert len(values) == 2
    week_tuple = eval(values[-1], {})
    assert len(week_tuple) == 10


def test_parse_schedule_week_pd2():
    """Test the parsing of WEEK-SCHEDULE-PD."""
    u_name, command, keywords, values = parse_inp_string(SCHEDULE_WEEK_PD_STR2)

    assert u_name == 'PRJ Heating Wk'
    assert command == 'WEEK-SCHEDULE-PD'
    assert len(keywords) == 2
    assert len(values) == 2
    week_tuple = eval(values[-1].replace('&D', '"&D"'), {})
    assert len(week_tuple) == 7


def test_parse_schedule_year():
    """Test the parsing of SCHEDULE."""
    u_name, command, keywords, values = parse_inp_string(SCHEDULE_YEAR_STR)

    assert u_name == 'College HTGSETP SCH'
    assert command == 'SCHEDULE'
    assert len(keywords) == 2
    assert len(values) == 2
    assert keywords[0] == 'TYPE'
    assert values[0] == 'TEMPERATURE'


def test_parse_schedule_year_pd():
    """Test the parsing of SCHEDULE-PD."""
    u_name, command, keywords, values = parse_inp_string(SCHEDULE_YEAR_PD_STR)

    assert u_name == 'PRJ Heating Sch'
    assert command == 'SCHEDULE-PD'
    assert len(keywords) == 4
    assert len(values) == 4
    assert keywords[0] == 'TYPE'
    assert values[0] == 'TEMPERATURE'


def test_parse_inp_file():
    """Test parsing of a DOE-2 INP file into object dict"""
    inp_file_path = os.path.join(os.path.dirname(__file__), 'assets', 'test_project.inp')
    inp_object_dict = parse_inp_file(inp_file_path)

    assert isinstance(inp_object_dict, dict)
    assert 'PARAMETER' in inp_object_dict or len(inp_object_dict) > 0

    assert 'SPACE' in inp_object_dict
    assert isinstance(inp_object_dict['SPACE'], dict)
    assert len(inp_object_dict['SPACE']) > 0

    known_space = 'L1WNE Perim Spc (G.NE1)' 
    assert known_space in inp_object_dict['SPACE']

    space_obj = inp_object_dict['SPACE'][known_space]
    assert isinstance(space_obj, dict)


inp_file_path = os.path.join(os.path.dirname(__file__), 'assets', 'test_project.inp')
inp_object_dict = parse_inp_file(inp_file_path)