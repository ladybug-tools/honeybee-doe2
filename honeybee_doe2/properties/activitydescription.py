from dataclasses import dataclass
from enum import Enum
import textwrap
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from typing import List
from typing import Set

from ..utils.doe_formatters import short_name


class DayScheduleType(Enum):
    """Enum to classify the type of a DaySchedule."""

    ONOFF = 'ON/OFF'
    """ accepts the binary values 0 and 1, where 0 means the schedule is OFF and 1
        means the schedule is ON. Examples include schedules for fans and
        heating/cooling availability.
    """
    FRACTION = 'FRACTION'
    """ accepts values between and including 0.0 and 1.0. Examples include lighting,
        people, etc
    """
    MULTIPLIER = 'MULTIPLIER'
    """accepts values 0.0 and above. Examples, include lighting, people, etc"""
    TEMPERATURE = 'TEMPERATURE'
    """ Accepts a value that represents a temperature. Examples include heating and
        cooling thermostat schedules.
    """
    RADIATION = 'RADIATION'
    """ accepts a value that represents a radiative flux, expressed in Btu/ft2-hr or W/m2.
        An example is the WINDOW:MAX-SOLAR-SCH.
    """
    ONOFFTEMP = 'ON/OFF/TEMP'
    """ accepts the binary values 0 and 1, similar to ON/OFF. Any other value is also
        acceptable, and is assumed to represent a flag temperature. When a temperature,
        the meaning of the value and its action varies by the component referencing the
        schedule. For example, in the SYSTEM:HEATING-SCHEDULE, the binary values 0 and
        1 disable and enable heating respectively. Any value other than 0 or 1 represents
        the outdoor drybulb temperature below which heating is enabled.
    """

    ONOFFFLAG = 'ON/OFF/FLAG'
    """ accepts the binary values 0 and 1, similar to ON/OFF. Any other value is also
        acceptable, and is assumed to represent a flag value. When a flag, the meaning of
        the value and its action varies by the keyword.
        For example, in the SYSTEM:NATURAL-VENT-SCH, a value of 0 forces the
        windows closed, and a value of 1 allows windows to be open if the outdoor
        temperature is suitable, and a flag value of –1 allows windows to be open if the
        outdoor enthalpy is also suitable.
    """
    FRACDESIGN = 'FRAC/DESIGN'
    """ accepts a value which is the fraction of the design quantity. Typical values range
        between 0.0 and 1.0. An entry of –999 causes the schedule to be ignored for that
        hour. For example, in the SYSTEM:MIN-AIR-SCH, an entry of 0 or 1 will force the
        outdoor-air ratio to be 0% or 100% respectively. A value of –999 will cause the
        schedule to be ignored for the hour, and the outdoor-air ratio will be set by other
        calculations.
    """
    EXPFRACTION = 'EXP-FRACTION'
    """ accepts a value between –1 and 1. An example is the WINDOW:SLAT-SCHEDULE."""

    FLAG = 'FLAG'
    """ accepts a flag of any value. The flag value must exactly match a comparison
        criterion for the component to be active. For example, in the ELEC-METER:COGEN-TRACK-SCH, a flag value of 1
        means that cogeneration equipment should track the electric load, a value of 2
        means track the thermal load, 3 means track the lesser of the electric or thermal
        load, etc.
    """
    RESETTEMP = 'RESET-TEMP'
    """ specifies that, rather than a 24-hour profile, that the DAY-SCHEDULE
        defines a relationship between the outside air temperature and a temperature
        setpoint, such as supply air temperature. Refer to the section below on “Reset
        Schedules” for more information. Note: TYPE = RESET-TEMP and RESET-RATIO work only in DAY-
        SCHEDULE-PD; not DAY-SCHEDULE. They replace the original DAY-RESET-SCH command that was used
        prior to the development of user interfaces.
    """
    RESETRATIO = 'RESET-RATIO'
    """ specifies that, rather than a 24-hour profile, that the DAY-SCHEDULE
        defines a relationship between the outside air temperature and a system control
        parameter, such as baseboard heating power. Refer to the section below on “Reset
        Schedules” for more information.
        Note: TYPE = RESET-TEMP and RESET-RATIO work only in DAY-
        SCHEDULE-PD; not DAY-SCHEDULE. They replace the original DAY-
        RESET-SCH command that was used prior to the development of user
        interfaces.
    """


@dataclass
class DayScheduleDoe:
    name: str = None
    values: [float] = None
    stype: DayScheduleType = None

    @classmethod
    def from_day_schedule(cls, day_schedule, stype):
        """Create a DaySchedule from a DaySchedule.
        """
        # TODO: format the output to look better, follow indent rules etc.

        mywrap = textwrap.TextWrapper(width=20)

        vals = list(day_schedule.data_collection().values)
        vals = ", ".join([str(val) for val in vals])
        vals = mywrap.fill(vals)

        return cls(name=short_name(day_schedule.display_name),
                   values=vals,
                   stype=stype)

    def to_inp(self):
        obj_lines = []
        obj_lines.append(f'"{self.name}" = DAY-SCHEDULE')
        obj_lines.append(f'\n   TYPE    = {self.stype.value}')
        obj_lines.append(f'\n   (1,24)    ({self.values})')
        obj_lines.append(f'\n   ..')

        return ''.join([line for line in obj_lines])

    def __repr__(self):
        return self.to_inp()


class Days(Enum):
    MON = "MON"
    """Monday"""
    TUE = "TUE"
    """Tuesday"""
    WED = "WED"
    """Wednesday"""
    THUR = "THUR"
    """Thursday"""
    FRI = "FRI"
    """Friday"""
    SAT = "SAT"
    """Saterday"""
    SUN = "SUN"
    """Sunday"""
    HOL = "HOL"
    """Holidays"""
    WD = "WD"
    """Weekdays (Mon-Fri)"""
    WEH = "WEH"
    """Weekends and holidays (Sat, Sun, Hol)"""
    HDD = "HDD"
    """Heating Design Day"""
    CDD = "CDD"
    """Cooling Design Day"""
    ALL = "ALL"
    """All 10 days in the week schedule (Mon-Sun, Hol, HDD, CDD)"""


@dataclass
class WeekScheduleDoe:
    name: str = None
    stype: str = DayScheduleType
    day_schedules: List = None

    @classmethod
    def from_schedule_ruleset(cls, stype, schedule_ruleset):
        """Create a WeekScheduleDoe from a ScheduleRuleset."""
        myruleset = schedule_ruleset
        name = short_name(schedule_ruleset.display_name)
        stype = stype

        days_of_the_week = ['monday', 'tuesday',
                            'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

        days = []
        for rule in myruleset:
            for day in days_of_the_week:
                if day in rule.days_applied:
                    days.append(short_name(rule.schedule_day.display_name)) if rule.schedule_day.display_name \
                        is not None else short_name(myruleset.default_day_schedule.display_name)
                else:
                    days.append(short_name(myruleset.default_day_schedule.display_name))

        if len(myruleset.schedule_rules) == 0:
            if len(myruleset.day_schedules) == 3:
                for day in days_of_the_week:
                    days.append(short_name(myruleset.default_day_schedule.display_name))
        
        if len(myruleset.day_schedules) == 1:
            for day in days_of_the_week:
                days.append(short_name(myruleset.default_day_schedule.display_name))     
        
        if myruleset.holiday_schedule is not None:
            days.append(short_name(myruleset.holiday_schedule.display_name))
        else:
            days.append(short_name(myruleset.default_day_schedule.display_name))
        
        if myruleset.winter_designday_schedule is not None:
            days.append(short_name(myruleset.winter_designday_schedule.display_name)) 
        else:
            days.append(short_name(myruleset.default_day_schedule.display_name))
        
        if myruleset.summer_designday_schedule is not None:
            days.append(short_name(myruleset.summer_designday_schedule.display_name))    
        else:
            days.append(short_name(myruleset.default_day_schedule.display_name))

        return cls(name=name, stype=stype, day_schedules=days)

    def to_inp(self):
        # TODO: fix the cause of the issue
        if len(self.day_schedules) < 8:
            print('Invalid day schedule with less than 8 values.')
            return ''

        obj_lines = []
        obj_lines.append(f'"{self.name}"      = WEEK-SCHEDULE-PD')
        obj_lines.append(f'\n   TYPE          = {self.stype.value}')
        obj_lines.append(f'\n   DAY-SCHEDULES = ( "{self.day_schedules[0]}", $ Monday')
        obj_lines.append(f'\n                     "{self.day_schedules[1]}", $ Tuesday')
        obj_lines.append(f'\n                     "{self.day_schedules[2]}", $ Wednesday')
        obj_lines.append(f'\n                     "{self.day_schedules[3]}", $ Thursday')
        obj_lines.append(f'\n                     "{self.day_schedules[4]}", $ Friday')
        obj_lines.append(f'\n                     "{self.day_schedules[5]}", $ Saturday')
        obj_lines.append(f'\n                     "{self.day_schedules[6]}", $ Sunday')
        obj_lines.append(f'\n                     "{self.day_schedules[7]}", $ Holiday')
        obj_lines.append(
            f'\n                     "{self.day_schedules[8]}", $ Winter Design Day')
        obj_lines.append(
            f'\n                     "{self.day_schedules[9]}", $ Summer Design Day')
        obj_lines.append(f'\n                    )')

        obj_lines.append(f'\n   ..\n')

        obj_lines.append(f'"{self.name}_" = SCHEDULE-PD')
        obj_lines.append(f'\n   TYPE     = {self.stype.value}')
        obj_lines.append(f'\n   MONTH    = 12')
        obj_lines.append(f'\n   DAY      = 31')
        obj_lines.append(f'\n   WEEK-SCHEDULES = "{self.name}"')
        obj_lines.append(f'\n   ..\n')

        return ''.join([line for line in obj_lines])

    def __repr__(self):
        return self.to_inp()
