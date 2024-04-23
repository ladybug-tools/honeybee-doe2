"""honeybee-doe2 load translators."""
from ladybug.datatype.area import Area
from ladybug.datatype.energyflux import EnergyFlux
from ladybug.datatype.volumeflowrateintensity import VolumeFlowRateIntensity
from honeybee.typing import clean_doe2_string

from .config import RES_CHARS

# TODO: Add methods to map to SOURCE-TYPE HOT-WATER and PROCESS


def people_to_inp(room):
    """Translate the People definition of a Room into INP (Keywords, Values)."""
    people = room.properties.energy.people
    ppl_den = Area().to_unit([people.area_per_person], 'ft2', 'm2')[0]
    ppl_total = ppl_den * room.floor_area
    ppl_sch = clean_doe2_string(people.occupancy_schedule.display_name, RES_CHARS)
    ppl_sch = '"{}"'.format(ppl_sch)
    ppl_kwd = ('NUMBER-OF-PEOPLE', 'PEOPLE-SCHEDULE')
    ppl_val = (ppl_total, ppl_sch)
    return ppl_kwd, ppl_val


def lighting_to_inp(room):
    """Translate the Lighting definition of a Room into INP (Keywords, Values)."""
    lighting = room.properties.energy.lighting
    lpd = EnergyFlux().to_unit([lighting.watts_per_area], 'W/ft2', 'W/m2')[0]
    lgt_sch = clean_doe2_string(lighting.schedule.display_name, RES_CHARS)
    lgt_sch = '"{}"'.format(lgt_sch)
    light_kwd = ('LIGHTING-W/AREA', 'LIGHTING-SCHEDULE', 'LIGHT-TO-RETURN')
    light_val = (lpd, lgt_sch, lighting.return_air_fraction)
    return light_kwd, light_val


def equipment_to_inp(room):
    """Translate the Equipment definition(s) of a Room into INP (Keywords, Values)."""
    # first evaluate what types of equipment we have
    ele_equip = room.properties.energy.electric_equipment
    gas_equip = room.properties.energy.gas_equipment

    # extract the properties from the equipment objects
    if ele_equip is not None and gas_equip is not None:  # write them as lists
        equip_val = [[], [], [], [], []]
        for equip in (ele_equip, gas_equip):
            epd = EnergyFlux().to_unit([equip.watts_per_area], 'W/ft2', 'W/m2')[0]
            equip_val[0].append(epd)
            eqp_sch = clean_doe2_string(equip.schedule.display_name, RES_CHARS)
            equip_val[1].append('"{}"'.format(eqp_sch))
            equip_val[2].append(1 - equip.latent_fraction - equip.lost_fraction)
            equip_val[3].append(equip.latent_fraction)
            equip_val[4].append(equip.radiant_fraction)
        equip_val = ['( {}, {} )'.format(v[0], v[1]) for v in equip_val]
    else:  # write them as a single item
        equip = ele_equip if gas_equip is None else gas_equip
        epd = EnergyFlux().to_unit([equip.watts_per_area], 'W/ft2', 'W/m2')[0]
        eqp_sch = clean_doe2_string(equip.schedule.display_name, RES_CHARS)
        eqp_sch = '"{}"'.format(eqp_sch)
        sens_fract = 1 - equip.latent_fraction - equip.lost_fraction
        equip_val = (epd, eqp_sch, sens_fract, equip.latent_fraction,
                     equip.radiant_fraction)

    equip_kwd = ('EQUIPMENT-W/AREA', 'EQUIPMENT-SCHEDULE',
                 'EQUIP-SENSIBLE', 'EQUIP-LATENT', 'EQUIP-RAD-FRAC')
    return equip_kwd, equip_val


def infiltration_to_inp(room):
    """Translate the Infiltration definition of a Room into INP (Keywords, Values)."""
    infil = room.properties.energy.infiltration
    inf_den = infil.flow_per_exterior_area
    inf_den = VolumeFlowRateIntensity().to_unit([inf_den], 'cfm/ft2', 'm3/s-m2')[0]
    inf_sch = clean_doe2_string(infil.schedule.display_name, RES_CHARS)
    inf_sch = '"{}"'.format(inf_sch)
    inf_kwd = ('INF-METHOD', 'INF-FLOW/AREA', 'INF-SCHEDULE')
    inf_val = ('AIR-CHANGE', inf_den, inf_sch)
    return inf_kwd, inf_val
