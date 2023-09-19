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
from .activitydescription import DayScheduleDoe, DayScheduleType, WeekScheduleDoe


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
    def hvac_sys_zones_by_model(self):
        hvac_sys = [HVACSystem.from_model(obj)]
        return hvac_sys

    @property
    def hvac_sys_zones_by_story(self):
        hvac_sys_zones = [HVACSystem.from_story(story) for story in self.stories]
        return hvac_sys_zones

    @property
    def hvac_sys_zones_by_room(self):
        hvac_sys_zones = [HVACSystem.from_room(room) for room in self.host.rooms]
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

    @property
    def week_scheduels(self):
        return self._get_week_scheduels(self.host)

    @staticmethod
    def _get_week_scheduels(obj):

        translated_schedules = []
        for room in obj.rooms:

            if room.properties.energy.lighting is not None:
                translated_schedules.append(
                    WeekScheduleDoe.from_schedule_ruleset(
                        schedule_ruleset=room.properties.energy.lighting.schedule,
                        stype=DayScheduleType.FRACTION))

            if room.properties.energy.people is not None:
                translated_schedules.append(
                    WeekScheduleDoe.from_schedule_ruleset(
                        schedule_ruleset=room.properties.energy.people.occupancy_schedule,
                        stype=DayScheduleType.FRACTION))

            if room.properties.energy.electric_equipment is not None:
                translated_schedules.append(
                    WeekScheduleDoe.from_schedule_ruleset(
                        schedule_ruleset=room.properties.energy.electric_equipment.schedule,
                        stype=DayScheduleType.FRACTION))

            if room.properties.energy.infiltration is not None:
                translated_schedules.append(
                    WeekScheduleDoe.from_schedule_ruleset(
                        schedule_ruleset=room.properties.energy.infiltration.schedule,
                        stype=DayScheduleType.MULTIPLIER)
                )

        if len(translated_schedules) > 0:
            return '\n'.join(
                set([schedule.to_inp() for schedule in translated_schedules]))
        elif len(translated_schedules) == 0:
            return '\n'

    @property
    def day_scheduels(self):
        return self._get_day_scheduels(self.host)

    @staticmethod
    def _get_day_scheduels(obj):

        translated_schedules = []
        for room in obj.rooms:

            if room.properties.energy.lighting is not None:
                for sch in room.properties.energy.lighting.schedule.day_schedules:
                    translated_schedules.append(
                        DayScheduleDoe.from_day_schedule(
                            day_schedule=sch, stype=DayScheduleType.FRACTION))

            if room.properties.energy.people is not None:
                for sch in room.properties.energy.people.occupancy_schedule.day_schedules:
                    translated_schedules.append(
                        DayScheduleDoe.from_day_schedule(
                            day_schedule=sch, stype=DayScheduleType.FRACTION))

            if room.properties.energy.electric_equipment is not None:
                for sch in room.properties.energy.electric_equipment.schedule.day_schedules:
                    translated_schedules.append(
                        DayScheduleDoe.from_day_schedule(
                            day_schedule=sch, stype=DayScheduleType.FRACTION))

            if room.properties.energy.infiltration is not None:
                for sch in room.properties.energy.infiltration.schedule.day_schedules:
                    translated_schedules.append(
                        DayScheduleDoe.from_day_schedule(
                            day_schedule=sch, stype=DayScheduleType.MULTIPLIER))

        if len(translated_schedules) > 0:
            return '\n'.join(
                set([schedule.to_inp() for schedule in translated_schedules]))
        elif len(translated_schedules) == 0:
            return '\n'

    def __str__(self):
        return "Model Doe2 Properties: [host: {}]".format(self.host.display_name)

    def __repr__(self):
        return str(self)

    def ToString(self):
        return self.__repr__()
