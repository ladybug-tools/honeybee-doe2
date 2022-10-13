# -*- coding: utf-8 -*-
# -*- Python Version: 2.7 -*

""" HB-Model Doe2 (eQuest) Properties."""
from .inputils import blocks as fb


class ModelDoe2Properties(object):
    """_summary_

    Args:
        object (_type_): _description_
    """

    def __init__(self, _host):
        self._host = _host

    @property
    def host(self):
        return self._host

    def duplicate(self, new_host=None):
        """_summary_
        Args:
            new_host (_type_, optional): _description_. Defaults to None.
        Returns:
            _type_: _description_
        """
        # type: (Any) -> ModelDoe2Properties
        _host = new_host or self._host
        new_properties_obj = ModelDoe2Properties(_host)
        return new_properties_obj

    @property
    def doe_stories(self):
        return self._make_doe_stories(self.host)

    @staticmethod
    def _make_doe_stories(obj):
        pass

    def to_inp_file(self):
        data = [
            self._header,
            fb.global_params,
            fb.ttrpddh, self.title.to_inp(), self.run_period.to_inp(),
            fb.comply,
            self.compliance_data.to_inp(),
            self.site_bldg_data.to_inp(),
            self.constructions.to_inp(),
            fb.glzCode,
            '\n'.join(gt.to_inp() for gt in self.glass_types),
            fb.polygons,
            '\n'.join(pl.to_inp() for pl in self.polygons),
            fb.wallParams,
            '\n'.join(shd.to_inp() for shd in self.context_shades),
            fb.miscCost,
            fb.perfCurve,
            fb.floorNspace,
            '\n'.join(flr.to_inp() for flr in self.floors),
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
            '\n'.join(hv_sys.to_inp() for hv_sys in self.hvac_system_zone),
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

    def __str__(self):
        return "Model Doe2 Properties: [host: {}]".format(self.host.display_name)

    def __repr__(self):
        return str(self)

    def ToString(self):
        return self.__repr__()
