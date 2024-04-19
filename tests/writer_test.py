"""Tests the features that honeybee_energy adds to honeybee_core Model."""
from ladybug_geometry.geometry3d import Point3D, Vector3D, Mesh3D

from honeybee.model import Model
from honeybee.room import Room
from honeybee.shademesh import ShadeMesh


def test_inp_writer():
    """Test the existence of the Model inp reiter."""
    room = Room.from_box('Tiny_House_Zone', 5, 10, 3)
    south_face = room[3]
    south_face.apertures_by_ratio(0.4, 0.01)
    south_face.apertures[0].overhang(0.5, indoor=False)
    south_face.apertures[0].overhang(0.5, indoor=True)
    south_face.apertures[0].move_shades(Vector3D(0, 0, -0.5))
    pts = (Point3D(0, 0, 4), Point3D(0, 2, 4), Point3D(2, 2, 4),
           Point3D(2, 0, 4), Point3D(4, 0, 4))
    mesh = Mesh3D(pts, [(0, 1, 2, 3), (2, 3, 4)])
    awning_1 = ShadeMesh('Awning_1', mesh)

    model = Model('Tiny_House', [room], shade_meshes=[awning_1])

    assert hasattr(model.to, 'inp')
