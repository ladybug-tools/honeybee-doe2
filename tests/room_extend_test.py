"""Tests the features that honeybee_doe2 adds to honeybee_core Room."""
from ladybug_geometry.geometry3d.pointvector import Point3D
from honeybee.room import Room
from honeybee_energy.lib.programtypes import office_program

from honeybee_doe2.properties.room import RoomDoe2Properties


def test_doe2_properties():
    """Test the existence of the Room energy properties."""
    room = Room.from_box('ShoeBox', 5, 10, 3, 90, Point3D(0, 0, 3))
    room.properties.energy.program_type = office_program
    room.properties.energy.add_default_ideal_air()

    assert hasattr(room.properties, 'doe2')
    assert isinstance(room.properties.doe2, RoomDoe2Properties)

    assert room.properties.doe2.assigned_flow is None
    room.properties.doe2.assigned_flow = 100
    assert room.properties.doe2.assigned_flow == 100

    assert room.properties.doe2.flow_per_area is None
    room.properties.doe2.flow_per_area = 1
    assert room.properties.doe2.flow_per_area == 1

    assert room.properties.doe2.min_flow_ratio is None
    room.properties.doe2.min_flow_ratio = 0.3
    assert room.properties.doe2.min_flow_ratio == 0.3

    assert room.properties.doe2.min_flow_per_area is None
    room.properties.doe2.min_flow_per_area = 0.35
    assert room.properties.doe2.min_flow_per_area == 0.35

    assert room.properties.doe2.hmax_flow_ratio is None
    room.properties.doe2.hmax_flow_ratio = 0.5
    assert room.properties.doe2.hmax_flow_ratio == 0.5


def test_duplicate():
    """Test what happens to doe2 properties when duplicating a Room."""
    room_original = Room.from_box('ShoeBox', 5, 10, 3)
    room_original.properties.energy.program_type = office_program
    room_original.properties.energy.add_default_ideal_air()

    room_dup_1 = room_original.duplicate()

    assert room_original.properties.doe2.assigned_flow == \
        room_dup_1.properties.doe2.assigned_flow
    assert room_original.properties.doe2.flow_per_area == \
        room_dup_1.properties.doe2.flow_per_area
    assert room_original.properties.doe2.min_flow_ratio == \
        room_dup_1.properties.doe2.min_flow_ratio
    assert room_original.properties.doe2.min_flow_per_area == \
        room_dup_1.properties.doe2.min_flow_per_area
    assert room_original.properties.doe2.hmax_flow_ratio == \
        room_dup_1.properties.doe2.hmax_flow_ratio

    room_original.properties.doe2.assigned_flow = 100
    room_original.properties.doe2.flow_per_area = 1
    room_original.properties.doe2.min_flow_ratio = 0.3
    room_original.properties.doe2.min_flow_per_area = 0.35
    room_original.properties.doe2.hmax_flow_ratio = 0.5

    assert room_original.properties.doe2.assigned_flow != \
        room_dup_1.properties.doe2.assigned_flow
    assert room_original.properties.doe2.flow_per_area != \
        room_dup_1.properties.doe2.flow_per_area
    assert room_original.properties.doe2.min_flow_ratio != \
        room_dup_1.properties.doe2.min_flow_ratio
    assert room_original.properties.doe2.min_flow_per_area != \
        room_dup_1.properties.doe2.min_flow_per_area
    assert room_original.properties.doe2.hmax_flow_ratio != \
        room_dup_1.properties.doe2.hmax_flow_ratio


def test_to_dict():
    """Test the Room to_dict method with doe2 properties."""
    room = Room.from_box('ShoeBox', 5, 10, 3)
    room.properties.energy.program_type = office_program
    room.properties.energy.add_default_ideal_air()
    room.properties.doe2.assigned_flow = 100
    room.properties.doe2.flow_per_area = 1
    room.properties.doe2.min_flow_ratio = 0.3
    room.properties.doe2.min_flow_per_area = 0.35
    room.properties.doe2.hmax_flow_ratio = 0.5

    rd = room.to_dict()
    assert 'properties' in rd
    assert rd['properties']['type'] == 'RoomProperties'
    assert 'doe2' in rd['properties']
    assert rd['properties']['doe2']['type'] == 'RoomDoe2Properties'
    assert rd['properties']['doe2']['assigned_flow'] == 100
    assert rd['properties']['doe2']['flow_per_area'] == 1
    assert rd['properties']['doe2']['min_flow_ratio'] == 0.3
    assert rd['properties']['doe2']['min_flow_per_area'] == 0.35
    assert rd['properties']['doe2']['hmax_flow_ratio'] == 0.5


def test_from_dict():
    """Test the Room from_dict method with doe2 properties."""
    room = Room.from_box('ShoeBox', 5, 10, 3)
    room.properties.energy.program_type = office_program
    room.properties.energy.add_default_ideal_air()
    room.properties.doe2.assigned_flow = 100
    room.properties.doe2.flow_per_area = 1
    room.properties.doe2.min_flow_ratio = 0.3
    room.properties.doe2.min_flow_per_area = 0.35
    room.properties.doe2.hmax_flow_ratio = 0.5

    rd = room.to_dict()
    new_room = Room.from_dict(rd)
    assert new_room.to_dict() == rd


def test_to_inp():
    """Test the Room to_inp method with doe2 properties."""
    room = Room.from_box('ShoeBox', 5, 10, 3)
    room.properties.energy.program_type = office_program
    room.properties.energy.add_default_ideal_air()

    hvac_kwd, hvac_val = room.properties.doe2.to_inp()
    assert hvac_kwd == []
    assert hvac_val == []

    room.properties.doe2.assigned_flow = 100.0
    room.properties.doe2.flow_per_area = 1.0
    room.properties.doe2.min_flow_ratio = 0.3
    room.properties.doe2.min_flow_per_area = 0.35
    room.properties.doe2.hmax_flow_ratio = 0.5
    hvac_kwd, hvac_val = room.properties.doe2.to_inp()
    assert hvac_kwd == ['ASSIGNED-FLOW', 'FLOW/AREA', 'MIN-FLOW-RATIO',
                        'MIN-FLOW/AREA', 'HMAX-FLOW-RATIO']
    assert hvac_val == [100.0, 1.0, 0.3, 0.35, 0.5]


def test_apply_properties_from_user_data():
    """Test the Room apply_properties_from_user_data method with doe2 properties."""
    room = Room.from_box('ShoeBox', 5, 10, 3)
    room.properties.energy.program_type = office_program
    room.properties.energy.add_default_ideal_air()
    room.user_data = {
        "ASSIGNED-FLOW": 100.0,
        "FLOW/AREA": 1.0,
        "MIN-FLOW-RATIO": 0.3,
        "MIN-FLOW/AREA": 0.35,
        "HMAX-FLOW-RATIO": 0.5
    }

    room.properties.doe2.apply_properties_from_user_data()
    assert room.properties.doe2.assigned_flow == 100
    assert room.properties.doe2.flow_per_area == 1
    assert room.properties.doe2.min_flow_ratio == 0.3
    assert room.properties.doe2.min_flow_per_area == 0.35
    assert room.properties.doe2.hmax_flow_ratio == 0.5
