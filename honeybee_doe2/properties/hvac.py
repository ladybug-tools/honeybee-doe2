from ..utils.doe_formatters import short_name
from .story import Doe2Story
from dataclasses import dataclass
from typing import List
from uuid import uuid4

from honeybee.model import Model as HBModel
from honeybee.room import Room
from honeybee.typing import clean_string


@dataclass
class Zone:

    name: str
    heating_setpoint: float
    cooling_setpoint: float

    @classmethod
    def from_room(cls, room: Room):
        if not isinstance(room, Room):
            raise ValueError(
                f'Unsupported type: {type(room)}\n'
                'Expected honeybee room'
            )

        name = short_name(clean_string(value=room.display_name).replace(' ', ''))

        if room.properties.energy.is_conditioned:
            heating_setpoint = room.properties.energy.program_type.setpoint.heating_setpoint
            cooling_setpoint = room.properties.energy.program_type.setpoint.cooling_setpoint
        else:
            heating_setpoint = 72
            cooling_setpoint = 75

        return cls(name=name, heating_setpoint=heating_setpoint,
                   cooling_setpoint=cooling_setpoint)

    def to_inp(self):
        inp_str = f'"{self.name} Zn"   = ZONE\n  ' \
            'TYPE             = UNCONDITIONED\n  ' \
            f'DESIGN-HEAT-T    = {self.heating_setpoint}\n  ' \
            f'DESIGN-COOL-T    = {self.cooling_setpoint}\n  ' \
            'SIZING-OPTION    = ADJUST-LOADS\n  ' \
            f'SPACE            = "{self.name}"\n  ..\n'
        return inp_str

    def __repr__(self) -> str:
        return self.to_inp()


@dataclass
class HVACSystem:
    """Placeholder HVAC system class, returns each floor as a doe2,
    HVAC system, with rooms as zones.
    Args:
        name: story display name
        zones: list of doe2.hvac.Zone objects serviced by the system
    Init method(s):
        1. from_model(model: HBModel) -> doe2_system
        2. from_story(story: Doe2Story) -> doe2_system
        3. from_room(room: Room) -> doe2_system
    """
    name: str
    zones: List[Zone]

    @classmethod
    def from_model(cls, model: HBModel):
        if not isinstance(model, HBModel):
            raise ValueError(
                f'Unsupported type: {type(model)}\n'
                'Expected honeybee.model.Model'
            )
        name = short_name(model.display_name)
        zones = [Zone.from_room(room) for room in model.rooms]
        return cls(name=name, zones=zones)

    @classmethod
    def from_story(cls, story: Doe2Story):
        if not isinstance(story, Doe2Story):
            raise ValueError(
                f'Unsupported type: {type(story)}\n'
                'Expected Doe2Story'
            )
        name = short_name(story.display_name)
        zones = [Zone.from_room(room) for room in story.rooms]
        return cls(name=name, zones=zones)

    @classmethod
    def from_room(cls, room: Room):
        if not isinstance(room, Room):
            raise ValueError(
                f'Unsupported type: {type(room)}\n'
                'Expected honeybee.room.Room'
            )
        name = short_name(room.display_name)
        zones = [Zone.from_room(room)]
        return cls(name=name, zones=zones)

    def to_inp(self):
        sys_str = f'"{self.name}_Sys (SUM)" = SYSTEM\n' \
            '   TYPE             = SUM\n' \
            '   HEAT-SOURCE      = NONE\n' \
            '   SYSTEM-REPORTS   = NO\n   ..\n'
        zones_str = '\n'.join(zone.to_inp() for zone in self.zones)
        inp_str = '\n'.join([sys_str, zones_str])
        return inp_str

    def __repr__(self):
        return self.to_inp()
