from properties.inputils import blocks as fb
from properties.inputils.compliance import ComplianceData
from progressbar.inputils.sitebldg import SiteBldgData as sbd
from properties.inputils.run_period import RunPeriod as rp
from properties.inputils.title import Title

from honeybee.model import Model

# Finally. Once again into the fray.

comp_data = ComplianceData()  # TODO Un-Hardcode
sb_data = sbd()  # TODO Un-Hardcode


def model_to_inp(hb_model):
    # type: (Model) -> str
    rp = RunPeriod()
    data = [
        hb_model._header,
        fb.global_params,
        fb.ttrpddh,
        Title(tile=str(hb_model.display_name)).to_inp(),
        rp.to_inp(),  # TODO unhardcode
        fb.comply,
        comp_data.to_inp(),
        sb_data.to_inp(),
        hb_model.constructions.to_inp(),  # TODO can reuse from hbdoe2
        fb.glzCode,
        # TODO Glass types (might be hardcoded in OG)
        '\n'.join(gt.to_inp() for gt in hb_model.glass_types),
        fb.polygons,
        '\n'.join(pl.to_inp() for pl in hb_model.polygons),
        fb.wallParams,
        # '\n'.join(shd.to_inp() for shd in hb_model.context_shades),  # TODO shade support
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
        '\n'.join(hv_sys.to_inp()
                  for hv_sys in hb_model.hvac_system_zone),  # TODO need to frame up
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
