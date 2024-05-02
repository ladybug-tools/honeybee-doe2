"""honeybee-doe2 load translators."""
from __future__ import division

from ladybug.datatype.area import Area
from ladybug.datatype.power import Power
from ladybug.datatype.energyflux import EnergyFlux
from ladybug.datatype.volumeflowrate import VolumeFlowRate
from ladybug.datatype.volumeflowrateintensity import VolumeFlowRateIntensity
from honeybee.typing import clean_doe2_string

from .config import RES_CHARS
# TODO: Implement the keys that Trevor wants:
# FLOW/AREA, ASSIGNED-FLOW, MIN-FLOW-RATIO, MIN-FLOW/AREA, HMAX-FLOW-RATIO
# TODO: Add methods to translate daylight sensors
# TODO: Add methods to map honeybee_energy process loads to SOURCE-TYPE PROCESS


def people_to_inp(people):
    """Translate a People definition into INP (Keywords, Values).

    Args:
        people: A honeybee-energy People definition. None is allowed.

    Returns:
        A tuple with two elements.

        -   keywords: A tuple of text strings for keywords related to defining
            people for a Space.

        -   values: A tuple of text strings that aligns with the keywords and
            denotes the value for each keyword.
    """
    if people is None:
        return (), ()
    ppl_den = Area().to_unit([people.area_per_person], 'ft2', 'm2')[0]
    ppl_den = round(ppl_den, 3)
    ppl_sch = clean_doe2_string(people.occupancy_schedule.identifier, RES_CHARS)
    ppl_sch = '"{}"'.format(ppl_sch)
    keywords = ('AREA/PERSON', 'PEOPLE-SCHEDULE')
    values = (ppl_den, ppl_sch)
    return keywords, values


def lighting_to_inp(lighting):
    """Translate a Lighting definition into INP (Keywords, Values).

    Args:
        lighting: A honeybee-energy Lighting definition. None is allowed.

    Returns:
        A tuple with two elements.

        -   keywords: A tuple of text strings for keywords related to defining
            lighting for a Space.

        -   values: A tuple of text strings that aligns with the keywords and
            denotes the value for each keyword.
    """
    if lighting is None:
        return (), ()
    lpd = EnergyFlux().to_unit([lighting.watts_per_area], 'W/ft2', 'W/m2')[0]
    lpd = round(lpd, 3)
    lgt_sch = clean_doe2_string(lighting.schedule.identifier, RES_CHARS)
    lgt_sch = '"{}"'.format(lgt_sch)
    keywords = ('LIGHTING-W/AREA', 'LIGHTING-SCHEDULE', 'LIGHT-TO-RETURN')
    values = (lpd, lgt_sch, lighting.return_air_fraction)
    return keywords, values


def equipment_to_inp(electric_equip, gas_equip=None):
    """Translate an Equipment definition(s) into INP (Keywords, Values).

    Args:
        electric_equip: A honeybee-energy ElectricEquipment definition. None is allowed.
        gas_equip: A honeybee-energy GasEquipment definition. None is allowed.

    Returns:
        A tuple with two elements.

        -   keywords: A tuple of text strings for keywords related to defining
            the equipment for a Space.

        -   values: A tuple of text strings that aligns with the keywords and
            denotes the value for each keyword.
    """
    # extract the properties from the equipment objects
    if electric_equip is not None and gas_equip is not None:  # write them as lists
        values = [[], [], [], [], []]
        for equip in (electric_equip, gas_equip):
            epd = EnergyFlux().to_unit([equip.watts_per_area], 'W/ft2', 'W/m2')[0]
            values[0].append(round(epd, 3))
            eqp_sch = clean_doe2_string(equip.schedule.identifier, RES_CHARS)
            values[1].append('"{}"'.format(eqp_sch))
            values[2].append(round(1 - equip.latent_fraction - equip.lost_fraction, 3))
            values[3].append(round(equip.latent_fraction, 3))
            values[4].append(round(equip.radiant_fraction, 3))
        format_values = []
        for v in values:
            if isinstance(v[0], str):  # make sure the schedules do not go past 100 chars
                format_values.append('({},\n{}{})'.format(v[0], ' ' * 31, v[1]))
            else:
                format_values.append('({}, {})'.format(v[0], v[1]))
        values = format_values
    elif electric_equip is not None or gas_equip is not None:  # write as a single item
        equip = electric_equip if gas_equip is None else gas_equip
        epd = EnergyFlux().to_unit([equip.watts_per_area], 'W/ft2', 'W/m2')[0]
        epd = round(epd, 3)
        eqp_sch = clean_doe2_string(equip.schedule.identifier, RES_CHARS)
        eqp_sch = '("{}")'.format(eqp_sch)
        sens_fract = 1 - equip.latent_fraction - equip.lost_fraction
        values = (epd, eqp_sch, sens_fract, equip.latent_fraction,
                  equip.radiant_fraction)
    else:  # no equipment assigned
        return (), ()

    keywords = ('EQUIPMENT-W/AREA', 'EQUIP-SCHEDULE',
                'EQUIP-SENSIBLE', 'EQUIP-LATENT', 'EQUIP-RAD-FRAC')
    return keywords, values


def hot_water_to_inp(hot_water, room_floor_area):
    """Translate a ServiceHotWater definition into INP (Keywords, Values).

    Args:
        hot_water: A honeybee-energy ServiceHotWater definition. None is allowed.
        room_floor_area: The host Room floor area in square feet, which will
            be used to convert the hot water flow per unit floor area to an
            absolute load in BTU/h.

    Returns:
        A tuple with two elements.

        -   keywords: A tuple of text strings for keywords related to defining
            the hot water SOURCE load for a Space.

        -   values: A tuple of text strings that aligns with the keywords and
            denotes the value for each keyword.
    """
    if hot_water is None:
        return (), ()
    flow_den = hot_water.flow_per_area  # L/h-m2
    flr_area = Area().to_unit([room_floor_area], 'm2', 'ft2')[0]  # m2
    total_flow = flow_den * flr_area  # L/h
    delta_t = 50  # assume the water heater must heat water from 10C to 60C
    c_water = 4.186 # J/g-C, the specific heat of water
    shw_heat = total_flow * c_water * delta_t  # J/h using Q = m * c * deltaT
    shw_heat = shw_heat / 3600.  # Watts
    shw_power = round(Power().to_unit([shw_heat], 'Btu/h', 'W')[0], 3)
    shw_sch = clean_doe2_string(hot_water.schedule.identifier, RES_CHARS)
    shw_sch = '"{}"'.format(shw_sch)
    keywords = ('SOURCE-TYPE', 'SOURCE-POWER', 'SOURCE-SCHEDULE',
                'SOURCE-SENSIBLE', 'SOURCE-RAD-FRAC', 'SOURCE-LATENT')
    values = ('HOT-WATER', shw_power, shw_sch,
              hot_water.sensible_fraction, 0, hot_water.latent_fraction)
    return keywords, values


def infiltration_to_inp(infiltration):
    """Translate an Infiltration definition into INP (Keywords, Values).

    Args:
        infiltration: A honeybee-energy Infiltration definition. None is allowed.

    Returns:
        A tuple with two elements.

        -   keywords: A tuple of text strings for keywords related to defining
            infiltration for a Space.

        -   values: A tuple of text strings that aligns with the keywords and
            denotes the value for each keyword.
    """
    if infiltration is None:
        return (), ()
    inf_den = infiltration.flow_per_exterior_area
    inf_den = VolumeFlowRateIntensity().to_unit([inf_den], 'cfm/ft2', 'm3/s-m2')[0]
    inf_den = round(inf_den, 3)
    inf_sch = clean_doe2_string(infiltration.schedule.identifier, RES_CHARS)
    inf_sch = '"{}"'.format(inf_sch)
    keywords = ('INF-METHOD', 'INF-FLOW/AREA', 'INF-SCHEDULE')
    values = ('AIR-CHANGE', inf_den, inf_sch)
    return keywords, values


def setpoint_to_inp(setpoint):
    """Translate a Setpoint definition into INP (Keywords, Values).
    
    Args:
        setpoint: A honeybee-energy Setpoint definition. None is allowed.

    Returns:
        A tuple with two elements.

        -   keywords: A tuple of text strings for keywords related to defining
            setpoints for a Zone.

        -   values: A tuple of text strings that aligns with the keywords and
            denotes the value for each keyword.
    """
    if setpoint is None:  # use some default setpoints
        return ('DESIGN-HEAT-T', 'DESIGN-COOL-T'), (72, 75)
    heat_setpt = round(setpoint.heating_setpoint * (9. / 5.) + 32., 2)
    cool_setpt = round(setpoint.cooling_setpoint * (9. / 5.) + 32., 2)
    heat_sch = clean_doe2_string(setpoint.heating_schedule.identifier, RES_CHARS)
    heat_sch = '"{}"'.format(heat_sch)
    cool_sch = clean_doe2_string(setpoint.cooling_schedule.identifier, RES_CHARS)
    cool_sch = '"{}"'.format(cool_sch)
    keywords = ('DESIGN-HEAT-T', 'DESIGN-COOL-T', 'HEAT-TEMP-SCH', 'COOL-TEMP-SCH')
    values = (heat_setpt, cool_setpt, heat_sch, cool_sch)
    return keywords, values


def ventilation_to_inp(ventilation):
    """Translate a Ventilation definition into INP (Keywords, Values).

    Args:
        ventilation: A honeybee-energy Ventilation definition. None is allowed.

    Returns:
        A tuple with two elements.

        -   keywords: A list of text strings for keywords related to defining
            ventilation for a Space.

        -   values: A list of text strings that aligns with the keywords and
            denotes the value for each keyword.
    """
    keywords, values = [], []
    if ventilation is None:
        return keywords, values
    # check the flow per person
    ppl_den = ventilation.flow_per_person
    if ppl_den != 0:
        keywords.append('OA-FLOW/PER')
        ppl_den = VolumeFlowRate().to_unit([ppl_den], 'cfm', 'm3/s')[0]
        values.append(round(ppl_den, 3))
    # check the flow per floor area
    vent_den = ventilation.flow_per_area
    if vent_den != 0:
        keywords.append('OA-FLOW/AREA')
        vent_den = VolumeFlowRateIntensity().to_unit([vent_den], 'cfm/ft2', 'm3/s-m2')[0]
        values.append(round(vent_den, 3))
    # check the air changes per hour
    ach = ventilation.air_changes_per_hour
    if ach != 0:
        keywords.append('OA-CHANGES')
        values.append(round(ach, 3))
    # check the flow per zone
    total_flow = ventilation.flow_per_zone
    if total_flow != 0:
        keywords.append('OUTSIDE-AIR-FLOW')
        total_flow = VolumeFlowRate().to_unit([total_flow], 'cfm', 'm3/s')[0]
        values.append(round(total_flow, 3))
    # check the schedule
    vent_sch = ventilation.schedule
    if vent_sch is not None:
        keywords.append('MIN-FLOW-SCH')
        vent_sch = clean_doe2_string(vent_sch.identifier, RES_CHARS)
        values.append('"{}"'.format(vent_sch))
    return keywords, values
