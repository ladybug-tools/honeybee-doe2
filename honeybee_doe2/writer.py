from properties.inputils import blocks as fb
from honeybee.model import Model
from properties.inputils.run_period import RunPeriod


def model_to_inp(hb_model):
    # type: (Model) -> str
    rp = RunPeriod()
    data = [
        hb_model._header,
        fb.global_params,
        fb.ttrpddh,
        hb_model.title.to_inp(),
        rp.to_inp(),  # TODO unhardcode
        fb.comply,
        hb_model.compliance_data.to_inp(),  # TODO remove from model properties
        hb_model.site_bldg_data.to_inp(),
        hb_model.constructions.to_inp(),
        fb.glzCode,
        '\n'.join(gt.to_inp() for gt in hb_model.glass_types),
        fb.polygons,
        '\n'.join(pl.to_inp() for pl in hb_model.polygons),
        fb.wallParams,
        '\n'.join(shd.to_inp() for shd in hb_model.context_shades),
        fb.miscCost,
        fb.perfCurve,
        fb.floorNspace,
        '\n'.join(flr.to_inp() for flr in hb_model.floors),
        fb.elecFuelMeter,
        fb.elec_meter,
        fb.fuel_meter,
        fb.master_meter,
        fb.hvac_circ_loop,
        fb.pumps,
        fb.heat_exch,
        fb.circ_loop,
        fb.chiller_objs,
        fb.boiler_objs,
        fb.dwh,
        fb.heat_reject,
        fb.tower_free,
        fb.pvmod,
        fb.elecgen,
        fb.thermal_store,
        fb.ground_loop_hx,
        fb.comp_dhw_res,
        fb.steam_cld_mtr,
        fb.steam_mtr,
        fb.chill_meter,
        fb.hvac_sys_zone,
        '\n'.join(hv_sys.to_inp() for hv_sys in hb_model.hvac_system_zone),
        fb.misc_meter_hvac,
        fb.equip_controls,
        fb.load_manage,
        fb.big_util_rate,
        fb.ratchets,
        fb.block_charge,
        fb.small_util_rate,
        fb.output_reporting,
        fb.loads_non_hrly,
        fb.sys_non_hrly,
        fb.plant_non_hrly,
        fb.econ_non_hrly,
        fb.hourly_rep,
        fb.the_end
    ]
    return '\n\n'.join(data)
