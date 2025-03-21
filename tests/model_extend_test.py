"""Tests the features that honeybee_doe2 adds to honeybee_core Model."""
from honeybee.room import Room
from honeybee.model import Model
from honeybee_energy.lib.programtypes import office_program


def test_from_dict():
    """Test the Room from_dict method with doe2 properties."""
    room = Room.from_box('ShoeBox', 5, 10, 3)
    room.properties.energy.program_type = office_program
    room.properties.energy.add_default_ideal_air()
    south_face = room[3]
    south_face.apertures_by_ratio(0.4, 0.01)
    south_face.apertures[0].overhang(0.5, indoor=False)
    south_face.apertures[0].overhang(0.5, indoor=True)

    room.properties.doe2.assigned_flow = 100
    room.properties.doe2.flow_per_area = 1
    room.properties.doe2.min_flow_ratio = 0.3
    room.properties.doe2.min_flow_per_area = 0.35
    room.properties.doe2.hmax_flow_ratio = 0.5

    model = Model('Tiny_House', [room])

    model_dict = model.to_dict()
    new_model = Model.from_dict(model_dict)
    assert new_model.to_dict() == model_dict

    new_room = new_model.rooms[0]
    assert new_room.properties.doe2.assigned_flow == 100
    assert new_room.properties.doe2.flow_per_area == 1
    assert new_room.properties.doe2.min_flow_ratio == 0.3
    assert new_room.properties.doe2.min_flow_per_area == 0.35
    assert new_room.properties.doe2.hmax_flow_ratio == 0.5
