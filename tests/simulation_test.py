# coding=utf-8
from honeybee_energy.simulation.runperiod import RunPeriod

from honeybee_doe2.simulation import SimulationPar, SiteData

DEFAULT_RUN_PERIOD = \
    '"Default Run Period" = RUN-PERIOD-PD\n' \
    '   BEGIN-MONTH              = 1\n' \
    '   BEGIN-DAY                = 1\n' \
    '   BEGIN-YEAR               = 2021\n' \
    '   END-MONTH                = 12\n' \
    '   END-DAY                  = 31\n' \
    '   END-YEAR                 = 2021\n' \
    '   ..\n' \
    '"Standard US Holidays" = HOLIDAYS\n' \
    '   LIBRARY-ENTRY            = "US"\n' \
    '   ..\n'
DEFAULT_SITE_DATA = \
        '"Site Data" = SITE-PARAMETERS\n' \
        '   ALTITUDE                 = 100\n' \
        '   C-STATE                  = 21\n' \
        '   C-WEATHER-FILE           = *TMY2\\HARTFOCT.bin*\n' \
        '   C-COUNTRY                = 1\n' \
        '   C-901-LOCATION           = 1092\n' \
        '   ..\n' \
        '"Building Data" = BUILD-PARAMETERS\n' \
        '   HOLIDAYS                 = "Standard US Holidays"\n' \
        '   ..\n'


def test_run_period_to_inp():
    """Test the RunPeriod to_inp method."""
    run_period = RunPeriod()
    inp_str = run_period.to_inp()
    assert inp_str == DEFAULT_RUN_PERIOD


def test_site_data_to_inp():
    """Test the SiteData to_inp method."""
    site_data = SiteData(100)
    inp_str = site_data.to_inp()
    assert inp_str == DEFAULT_SITE_DATA


def test_simulation_par_to_inp():
    """Test the SimulationPar to_inp method."""
    title = 'Sample Project'
    simulation_par = SimulationPar(title)
    simulation_par.site.altitude = 100
    inp_str = simulation_par.to_inp()

    assert title in inp_str
    assert DEFAULT_RUN_PERIOD in inp_str
    assert DEFAULT_SITE_DATA in inp_str
    assert inp_str.endswith('PROJECT-DATA\n   ..\n')


def test_simulation_par_init():
    """Test the initialization of SimulationPar and basic properties."""
    sim_par = SimulationPar()
    str(sim_par)  # test the string representation

    assert sim_par.title == 'Unnamed'
    assert sim_par.run_period == RunPeriod()
    assert sim_par.site == SiteData()

    sim_par_dup = sim_par.duplicate()
    sim_par_alt = SimulationPar(title='Sample Project')
    assert sim_par is sim_par
    assert sim_par is not sim_par_dup
    assert sim_par == sim_par_dup
    sim_par_dup.title = 'test'
    assert sim_par != sim_par_dup
    assert sim_par != sim_par_alt


def test_simulation_parameter_to_dict_methods():
    """Test the to/from dict methods."""
    sim_par = SimulationPar()
    sim_par_dict = sim_par.to_dict()

    assert 'title' in sim_par_dict
    assert 'run_period' in sim_par_dict
    assert 'site' in sim_par_dict

    new_sim_par = SimulationPar.from_dict(sim_par_dict)
    assert new_sim_par == sim_par
    assert sim_par_dict == new_sim_par.to_dict()
