# -*- coding: utf-8 -*-
from honeybee.boundarycondition import Ground, Outdoors
from honeybee.facetype import Wall, Floor, RoofCeiling
from honeybee.face import Face
from honeybee.room import Room, Point3D
from typing import List

from ..utils.doe_formatters import short_name
from ..utils.geometry import get_floor_boundary, get_room_rep_poly
from .wall import DoeWall
from .roof import DoeRoof
from .groundcontact import GroundFloor
from.exposedfloor import ExposedFloor


class RoomDoe2Properties(object):
    """Properties for a DOE2 Space."""

    def __init__(self, _host: Room):
        self._host = _host

    @property
    def host(self) -> Room:
        return self._host

    @property
    def boundary(self) -> Face:
        return self._get_boundary_geometry(self._host)

    @property
    def origin(self) -> Point3D:
        """Origin point of the room."""
        return self.boundary.geometry.lower_left_corner

    def duplicate(self, new_host=None):

        _host = new_host or self._host
        new_properties_obj = RoomDoe2Properties(_host)
        return new_properties_obj

    @property
    def poly(self):
        # * return self's floor's face's poly
        return self.boundary.properties.doe2.poly

    @staticmethod
    def _get_boundary_geometry(room: Room):
        return get_room_rep_poly(room)

    @property
    def walls(self) -> List[DoeWall]:
        # * Needs to return list of DoeWall objects

        walls = [
            DoeWall(face) for face in self.host.faces
            if isinstance(face.type, Wall)
        ]
        return walls

    @property
    def roofs(self) -> List[DoeRoof]:
        roofs = [
            DoeRoof(face) for face in self.host.faces
            if isinstance(face.type, RoofCeiling)
        ]
        return roofs

    @property
    def ground_contact_surfaces(self):
        ground_contact_faces = [
            GroundFloor(face) for face in self.host.faces
            if isinstance(face.type, Floor)
            and isinstance(face.boundary_condition, Ground)
        ]

        return ground_contact_faces

    @property
    def exposed_floor_surfaces(self):
        exposed_floor_surfaces = [
            ExposedFloor(face) for face in self.host.faces
            if isinstance(face.type, Floor)
            and isinstance(face.boundary_condition, Outdoors)
        ]
        return exposed_floor_surfaces

    @property
    def window(self):
        pass
    # TODO add window support

    @property
    def door(self):
        pass
    # TODO add door support

    @property
    def activity_disc(self):
        pass
    # TODO add activity disc // loads support etc

    def space(self, floor_origin):

        floor_face = self.boundary
        azimuth = floor_face.azimuth
        # this value should be set in relation to the Floor object
        origin_pt = self.origin - floor_origin
        obj_lines = []
        obj_lines.append('"{}" = SPACE\n'.format(short_name(self.host.display_name)))
        obj_lines.append('   SHAPE           = POLYGON\n')
        obj_lines.append('   POLYGON         = "{} Plg"\n'.format(
            self.boundary.display_name))
        obj_lines.append('   AZIMUTH         = {}\n'.format(azimuth))
        obj_lines.append('   X               = {}\n'.format(origin_pt.x))
        obj_lines.append('   Y               = {}\n'.format(origin_pt.y))
        obj_lines.append('   Z               = {}\n'.format(origin_pt.z))
        obj_lines.append('   VOLUME          = {}\n'.format(self.host.volume))
        obj_lines.append('  ..\n')
        # obj_lines.append('   C-ACTIVITY-DESC = *{}*\n   ..\n'.format(str(obj.properties.energy.program_type)))
        spaces = ''.join(obj_lines)
        walls = '\n'.join([w.to_inp(self.origin) for w in self.walls])
        roofs = '\n'.join([r.to_inp(self.origin) for r in self.roofs])
        ground_floors = '\n'.join(
            [g.to_inp(self.origin) for g in self.ground_contact_surfaces]
        )
        exposed_floors = '\n'.join(
            [ef.to_inp(self.origin) for ef in self.exposed_floor_surfaces]
        )
        return '\n'.join([spaces, walls, roofs, ground_floors, exposed_floors])
