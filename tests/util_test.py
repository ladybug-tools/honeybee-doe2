"""Test the utility functions."""
import os
from honeybee_doe2.util import parse_inp_string, \
    resolve_defaults, find_user_lib_file

from honeybee_doe2.reader import command_dict_from_inp


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


def test_resolve_defaults_system_psz():
    """Test the resolve_defaults function for PSZ SYSTEM objects from
    int_loads_assigned.inp."""
    # Get the path to the test asset file
    this_dir = os.path.dirname(__file__)
    inp_file = os.path.join(this_dir, 'assets', 'int_loads_assigned.inp')

    # Read and parse the INP file
    with open(inp_file, 'r') as f:
        inp_content = f.read()
    cmd_dict = command_dict_from_inp(inp_content)

    # Get the SYSTEM defaults for PSZ type
    system_defaults = cmd_dict.get('DEFAULTS', {}).get(('SYSTEM', 'PSZ'), {})
    assert system_defaults is not None
    assert len(system_defaults) > 0

    # Get a specific SYSTEM object ("ac_")
    system_objects = cmd_dict.get('SYSTEM', {})
    assert 'ac_' in system_objects
    ac_attrs = system_objects['ac_']

    # Define some keys to resolve
    system_keys = [
        'TYPE', 'HEAT-SOURCE', 'RETURN-AIR-PATH', 'HEATING-SCHEDULE',
        'SUPPLY-KW/FLOW', 'COOL-CAP-FT', 'COOLING-EIR', 'COOL-EIR-FT',
        'COOL-EIR-FPLR', 'COOL-FT-MIN', 'MIN-AIR-SCH', 'FAN-SCHEDULE',
        'CONTROL-ZONE'
    ]

    # Resolve defaults for this system
    resolved = resolve_defaults(ac_attrs, system_defaults, system_keys)

    # Verify that values from both defaults and instance are present
    assert 'TYPE' in resolved
    assert resolved['TYPE'] == 'PSZ'

    # MIN-AIR-SCH and FAN-SCHEDULE should come from the SYSTEM keywords
    assert 'MIN-AIR-SCH' in resolved
    assert '"MNECB-97 A-Office Min OA Sch"' in str(resolved['MIN-AIR-SCH'])

    # SUPPLY-KW/FLOW should come from defaults
    assert 'SUPPLY-KW/FLOW' in resolved
    assert resolved['SUPPLY-KW/FLOW'] == 0.00025


def test_find_user_lib_file():
    """Test the find_user_lib_file function."""
    result = find_user_lib_file()

    # Result should be either None or a valid path string
    assert result is None or isinstance(result, str)

    if result is not None:
        # If a path is returned, verify it exists and has correct filename
        assert os.path.isfile(result), \
            'Returned path does not exist: {}'.format(result)
        assert result.endswith('eQ_Lib.dat'), \
            'Returned path does not end with eQ_Lib.dat: {}'.format(result)
