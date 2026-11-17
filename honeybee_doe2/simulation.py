# coding=utf-8
"""honeybee-doe2 simulation parameters."""
from __future__ import division
import math

from ladybug_geometry.geometry2d.pointvector import Vector2D
from ladybug.datatype.distance import Distance
from ladybug.location import Location
from ladybug.projectinfo import ProjectInfo
from honeybee.typing import clean_doe2_string, int_in_range
from honeybee_energy.simulation.runperiod import RunPeriod

from .config import GEO_CHARS
from .util import generate_inp_string, header_comment_minor


class SimulationPar(object):
    """Complete set of DOE-2 Simulation Settings.

    Args:
        title: Text for the title of the project. (Default: *Unnamed*).
        run_period: A honeybee-energy RunPeriod object to describe the time period
            over which to run the simulation. (Default: Run for the whole year).
        site: A SiteData object describing the site where the simulation is
            run. (Default: Hartford, CT).

    Properties:
        * title
        * run_period
        * site
    """
    __slots__ = ('_title', '_run_period', '_site')

    def __init__(self, title='Unnamed', run_period=None, site=None):
        """Initialize SimulationPar."""
        self.title = title
        self.run_period = run_period
        self.site = site

    @classmethod
    def from_dict(cls, data):
        """Create a SimulationPar object from a dictionary.

        Args:
            data: A SimulationPar dictionary in following the format below.

        .. code-block:: python

            {
            "type": "SimulationPar",
            "title": 'sample_project', # Text for the title
            "run_period": {}, # Honeybee RunPeriod dictionary
            "site": {}, # Honeybee SiteData dictionary
            }
        """
        assert data['type'] == 'SimulationPar', \
            'Expected SimulationPar dictionary. Got {}.'.format(data['type'])
        title = data['title'] if 'title' in data else 'Unnamed'
        run_period = None
        if 'run_period' in data and data['run_period'] is not None:
            run_period = RunPeriod.from_dict(data['run_period'])
        site = None
        if 'site' in data and data['site'] is not None:
            site = SiteData.from_dict(data['site'])
        return cls(title, run_period, site)

    @property
    def title(self):
        """Get or set text for the title of the project."""
        return self._title

    @title.setter
    def title(self, value):
        if value:
            value = clean_doe2_string(value, GEO_CHARS)
        else:
            value = None
        self._title = value

    @property
    def run_period(self):
        """Get or set a RunPeriod object for the time period to run the simulation."""
        return self._run_period

    @run_period.setter
    def run_period(self, value):
        if value is not None:
            assert isinstance(value, RunPeriod), 'Expected RunPeriod for ' \
                'SimulationPar run_period. Got {}.'.format(type(value))
            self._run_period = value
        else:
            self._run_period = RunPeriod()

    @property
    def site(self):
        """Get or set a SiteData object for the project site of the simulation."""
        return self._site

    @site.setter
    def site(self, value):
        if value is not None:
            assert isinstance(value, SiteData), 'Expected SiteData for ' \
                'SimulationPar site. Got {}.'.format(type(value))
            self._site = value
        else:
            self._site = SiteData()

    def to_inp(self):
        """Get an DOE-2 INP string representation of the SimulationPar."""
        # add the starting headers
        sp_str = []
        sp_str.append(header_comment_minor('Abort, Diagnostics'))
        sp_str.append(header_comment_minor('Global Parameters'))
        sp_str.append(header_comment_minor('Title, Run Periods, Design Days, Holidays'))
        # add the title and run period
        title_str = \
            'TITLE\n' \
            '   LINE-1           = *{}*\n' \
            '   ..\n'.format(self.title)
        sp_str.append(title_str)
        sp_str.append(self.run_period.to_inp())
        # add the site and building data
        sp_str.append(header_comment_minor('Compliance Data'))
        sp_str.append(header_comment_minor('Site and Building Data'))
        sp_str.append(self.site.to_inp())
        return '\n'.join(sp_str)

    def to_dict(self):
        """SimulationPar dictionary representation."""
        return {
            'type': 'SimulationPar',
            'title': self.title,
            'run_period': self.run_period.to_dict(),
            'site': self.site.to_dict(),
        }

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __copy__(self):
        return SimulationPar(
            self.title, self.run_period.duplicate(), self.site.duplicate())

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.title, hash(self.run_period), hash(self.site))

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, SimulationPar) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'DOE-2 SimulationPar: {}'.format(self.title)


class SiteData(object):
    """Object to describe the project site of the simulation.

    Args:
        north_angle: North angle in degrees. A number between -360 and 360 for the
            counterclockwise difference between the North and the positive Y-axis in
            degrees. 90 is West and 270 is East (Default: 0).
        location: An optional Ladybug Location object to describe the exact latitude,
            longitude, time zone and elevation of the project site. If None
            the location specified within the EPW file will be used for the
            simulation. (Default: None).

    Properties:
        * north_angle
        * north_vector
        * location
    """
    __slots__ = ('_north_angle', '_north_vector', '_location')

    def __init__(self, north_angle=0, location=None):
        """Initialize SiteData."""
        self.north_angle = north_angle
        self.location = location

    @property
    def north_angle(self):
        """Get or set a number between -360 and 360 for the north direction in degrees.

        This is the counterclockwise difference between the North and the positive
        Y-axis. 90 is West and 270 is East (Default: 0).
        """
        return self._north_angle

    @north_angle.setter
    def north_angle(self, value):
        self._north_angle = int_in_range(value, -360, 360, 'north angle')
        self._north_vector = Vector2D(0, 1).rotate(math.radians(self._north_angle))

    @property
    def north_vector(self):
        """Get or set a ladybug_geometry Vector2D for the north direction."""
        return self._north_vector

    @north_vector.setter
    def north_vector(self, value):
        assert isinstance(value, Vector2D), \
            'Expected Vector2D for north_vector. Got {}.'.format(type(value))
        self._north_vector = value
        self._north_angle = \
            math.degrees(self._north_vector.angle_clockwise(Vector2D(0, 1)))

    @property
    def location(self):
        """Get or set an optional Location object to override that within the EPW."""
        return self._location

    @location.setter
    def location(self, value):
        if value is not None:
            assert isinstance(value, Location), 'Expected Location ' \
                'for SiteData location. Got {}.'.format(type(value))
        self._location = value

    def assign_from_project_info(self, project_info, overwrite=False):
        """Assign attributes to this SiteData from a ladybug ProjectInfo.

        Args:
            project_info: A ladybug ProjectInfo object to be used to set
                simulation parameters.
            overwrite: Boolean to note whether existing attributes on this
                SiteData should be overwritten with the information in the ProjectInfo.
                When False, the Location will only be assigned if it is not already
                specified. When True, all existing attributes are overwritten
                (including the north attribute) is set according to whatever
                the ProjectInfo dictates.
        """
        # check that a ProjectInfo instance has been passes
        assert isinstance(project_info, ProjectInfo), \
            'Expected ProjectInfo. Got {}.'.format(type(project_info))
        if overwrite:  # overwrite existing attributes
            self.north_angle = project_info.north_angle
            self.location = project_info.location
        else:  # only assign attributes if they exist
            if not self.location:
                self.location = project_info.location

    @classmethod
    def from_project_info(cls, project_info):
        """Create a SimulationParameter object from a ladybug ProjectInfo.

        Args:
            project_info: A ladybug ProjectInfo object to be used to set
                simulation parameters.
        """
        sim_par = cls()
        sim_par.assign_from_project_info(project_info, True)
        return sim_par

    @classmethod
    def from_dict(cls, data):
        """Create a SiteData object from a dictionary.

        Args:
            data: A SiteData dictionary in following the format below.

        .. code-block:: python

            {
            "type": "SiteData",
            "north_angle": 15, # North angle in degrees
            "location": {} # Ladybug Location dictionary
            }
        """
        assert data['type'] == 'SiteData', \
            'Expected SiteData dictionary. Got {}.'.format(data['type'])
        north_angle = 0
        if 'north_angle' in data and data['north_angle'] is not None:
            north_angle = data['north_angle']
        location = None
        if 'location' in data and data['location'] is not None:
            location = Location.from_dict(data['location'])
        return cls(north_angle, location)

    def to_inp(self):
        """Get an DOE-2 INP string representation of the SiteData."""
        # create the INP string for the site
        if self.location is None:  # use the default Hartford, CT location
            keywords = ('ALTITUDE', 'C-STATE', 'C-WEATHER-FILE',
                        'C-COUNTRY', 'C-901-LOCATION')
            values = ('150', '21', '*TMY2\\HARTFOCT.bin*', '1', '1092')
        else:
            loc = self.location
            elev = int(Distance().to_unit([loc.elevation], 'ft', 'm')[0])
            keywords = ('LATITUDE', 'LONGITUDE', 'ALTITUDE', 'TIME-ZONE')
            values = (round(loc.latitude, 2), round(-loc.longitude, 2), elev, -loc.time_zone)
        site_str = generate_inp_string('Site Data', 'SITE-PARAMETERS', keywords, values)
        # create the INP string for the building data
        keywords = ('AZIMUTH', 'HOLIDAYS')
        values = (self.north_angle, '"Standard US Holidays"',)
        bldg_str = generate_inp_string(
            'Building Data', 'BUILD-PARAMETERS', keywords, values)
        return site_str + bldg_str

    def to_dict(self):
        """SiteData dictionary representation."""
        loc = self.location.to_dict() if self.location is not None else None
        return {
            'type': 'SiteData',
            'north_angle': self.north_angle,
            'location': loc
        }

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __copy__(self):
        return SiteData(self.north_angle, self.location)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.north_angle, hash(self.location))

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, SiteData) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.to_inp()


def run_period_to_inp(run_period):
    """Translate a honeybee-energy RunPeriod object to a DOE-2 INP string"""
    # create the string for the run period
    year = 2020 if run_period.is_leap_year else 2021
    keywords = ('BEGIN-MONTH', 'BEGIN-DAY', 'BEGIN-YEAR',
                'END-MONTH', 'END-DAY', 'END-YEAR')
    values = (run_period.start_date.month, run_period.start_date.day, year,
              run_period.end_date.month, run_period.end_date.day, year)
    rp_str = generate_inp_string('Default Run Period', 'RUN-PERIOD-PD', keywords, values)
    # create the string for the holidays
    keywords, values = ('LIBRARY-ENTRY',), ('"US"',)
    hol_str = generate_inp_string('Standard US Holidays', 'HOLIDAYS', keywords, values)
    return rp_str + hol_str
