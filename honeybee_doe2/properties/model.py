# -*- coding: utf-8 -*-
# -*- Python Version: 2.7 -*

""" HB-Model Doe2 (eQuest) Properties."""
from collections import defaultdict

from honeybee.model import Model
from honeybee.room import Room
from honeybee.face import Face

from .inputils import blocks as fb
from .inputils.compliance import ComplianceData
from .inputils.sitebldg import SiteBldgData as sbd
from .inputils.run_period import RunPeriod
from .inputils.title import Title


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
    def _header(self):
        """File header.
        NOTE: The header is currently read-only
        """
        return '\n'.join([fb.top_level, fb.abort_diag])

    @property
    def stories(self):
        return self._make_doe_stories(self.host)

    @staticmethod
    def _make_doe_stories(obj):
        grouped_rooms, flr_hgts = Room.group_by_floor_height(obj.rooms, 0.1)
        return grouped_rooms

    @property
    def polygons(self):
        return self._inp_polyblock_maker(self.host)

    @staticmethod
    def _inp_polyblock_maker(obj):
        inp_block = '\n'
        inp_polys = []
        for room in obj.rooms:
            for face in obj.faces:  # eQuest can have interior walls
                inp_polys.append(face.properties.doe2.poly)
        final_form = inp_block.join(pol for pol in inp_polys)
        return final_form  # I don't even know what I'm making a reference to tbh

    @property
    def header(self):
        return '\n'.join([fb.top_level, fb.abort_diag])

    def to_inp(self):
        rp = RunPeriod()  # TODO unhardcode: ext comp take lb.rp obj for DT
        comp_data = ComplianceData()
        sb_data = sbd()

        data = [
            hb_model.properties.doe2._header,
            fb.global_params,
            fb.ttrpddh,
            Title(title=str(hb_model.display_name)).to_inp(),
            rp.to_inp(),  # TODO unhardcode
            fb.comply,
            comp_data.to_inp(),
            sb_data.to_inp(),
            #        hb_model.constructions.to_inp(),  # TODO can reuse from dfdoe2
            fb.glzCode,
            # TODO add glass types to hb model doe2 properties
            #        '\n'.join(gt.to_inp() for gt in hb_model.glass_types),
            fb.polygons,
            hb_model.properties.doe2.polygons,
            fb.wallParams,
            # '\n'.join(shd.to_inp() for shd in hb_model.context_shades),  # TODO shade support
            fb.miscCost,
            fb.perfCurve,
            fb.floorNspace,
            #        '\n'.join(flr.to_inp() for flr in hb_model.floors),  # TODO floor object
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
            #        '\n'.join(hv_sys.to_inp()
            #                  for hv_sys in hb_model.hvac_system_zone),  # TODO need to frame up hvac
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
        return str('\n\n'.join(data))

    def __str__(self):
        return "Model Doe2 Properties: [host: {}]".format(self.host.display_name)

    def __repr__(self):
        return str(self)

    def ToString(self):
        return self.__repr__()
