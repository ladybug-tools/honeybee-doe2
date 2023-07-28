# -*- coding: utf-8 -*-
# -*- Python Version: 2.7 -*

""" HB-Model Doe2 (eQuest) Properties."""
from collections import defaultdict

from honeybee.model import Model
from honeybee.room import Room
from honeybee.face import Face
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.lib.constructionsets import generic_construction_set

from .inputils import blocks as fb
from .inputils.compliance import ComplianceData
from .inputils.sitebldg import SiteBldgData as sbd
from .inputils.run_period import RunPeriod
from .inputils.title import Title

from .story import Doe2Story
from .constructions import Construction, ConstructionCollection

from .hvac import HVACSystem, Zone
from .shades import Doe2Shade, Doe2ShadeCollection


class ModelDoe2Properties(object):
    """_summary_

    Args:
        object (_type_): _description_
    """

    def __init__(self, _host: Model):
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
        # * do tuple, (geom, 'space room whatever') for each 'inpblock' per story
        stories = []
        model = self.host
        tol = model.tolerance
        if not model.rooms:
            return stories
        grouped = Room.group_by_floor_height(model.rooms, 0.1)
        for i, story in enumerate(grouped[0]):
            stories.append(Doe2Story(story, i, tolerance=tol))

        return stories

    @property
    def header(self):
        return '\n'.join([fb.top_level, fb.abort_diag])

    @property
    def mats_cons_layers(self):
        return self._make_mats_cons_layers(self.host)

    @staticmethod
    def _make_mats_cons_layers(obj):
        cons = []
        for construction in generic_construction_set.wall_set.constructions:
            if isinstance(construction, OpaqueConstruction):
                cons.append(construction)
        for construction in generic_construction_set.floor_set.constructions:
            if isinstance(construction, OpaqueConstruction):
                cons.append(construction)
        for construction in generic_construction_set.roof_ceiling_set.constructions:
            if isinstance(construction, OpaqueConstruction):
                cons.append(construction)
        for construction in obj.properties.energy.constructions:
            if isinstance(construction, OpaqueConstruction):
                cons.append(construction)
        return ConstructionCollection.from_hb_constructions(constructions=cons).to_inp()

    @property
    def hvac_sys_zones(self):
        return self._get_hvac_sys_zones(self.stories)

    @staticmethod
    def _get_hvac_sys_zones(stories):
        hvac_sys_zones = [HVACSystem.from_story(story) for story in stories]
        return hvac_sys_zones

    @property
    def fixed_shades(self):
        return self._get_fixed_shades(self.host)

    @staticmethod
    def _get_fixed_shades(obj):
        if obj.shades is not None:
            return Doe2ShadeCollection.from_hb_shades(obj.shades).to_inp()
        else:
            return None

    def __str__(self):
        return "Model Doe2 Properties: [host: {}]".format(self.host.display_name)

    def __repr__(self):
        return str(self)

    def ToString(self):
        return self.__repr__()
