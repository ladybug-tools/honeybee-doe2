# -*- coding: utf-8 -*-
from honeybee_energy.boundarycondition import Adiabatic

from honeybee.boundarycondition import Ground, Outdoors, Surface
from honeybee.facetype import Wall, Floor, RoofCeiling
from honeybee.face import Face
from honeybee.room import Room
from typing import List
from uuid import uuid4

from ..utils.doe_formatters import short_name
from .wall import DoeWall
from .roof import DoeRoof
from .groundcontact import GroundFloor
from .exposedfloor import ExposedFloor
from .interiorfloor import InteriorFloor
from .adiabaticfloor import AdiabaticFloor
from .adiabaticroof import AdiabaticRoof


class RoomDoe2Properties(object):
    """Properties for a DOE2 Space."""

    def __init__(self, _host: Room):
        self._host = _host
        self._boundary = None

    @property
    def host(self) -> Room:
        return self._host

    def boundary(self, tolerance) -> Face:
        if self._boundary:
            return self._boundary
        tol = tolerance
        _boundary = self._host.horizontal_boundary(match_walls=False, tolerance=tol)
        _boundary = _boundary.remove_colinear_vertices(tolerance=tol)
        boundary_face = Face(identifier=str(uuid4()), geometry=_boundary)
        boundary_face.display_name = self._host.display_name
        self._boundary = boundary_face
        return boundary_face

    def duplicate(self, new_host=None):

        _host = new_host or self._host
        new_properties_obj = RoomDoe2Properties(_host)
        return new_properties_obj

    def poly(self, tolerance):
        # * return self's floor's face's poly
        return self.boundary(tolerance).properties.doe2.poly

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
            and isinstance(face.boundary_condition, (Outdoors, Surface))
        ]
        return roofs

    @property
    def adiabatic_roofs(self):
        adiabatic_roofs = [
            AdiabaticRoof(face) for face in self.host.faces
            if isinstance(face.type, RoofCeiling)
            and isinstance(face.boundary_condition, Adiabatic)

        ]
        return adiabatic_roofs

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
    def interior_floor_surfaces(self):
        interior_floor_surfaces = [
            InteriorFloor(face) for face in self.host.faces
            if isinstance(face.type, Floor)
            and isinstance(face.boundary_condition, Surface)
        ]
        return interior_floor_surfaces

    @property
    def adiabatic_floor_surfaces(self):
        adiabatic_floor_surfaces = [
            AdiabaticFloor(face) for face in self.host.faces
            if isinstance(face.type, Floor)
            and isinstance(face.boundary_condition, Adiabatic)
        ]
        return adiabatic_floor_surfaces

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
        # chances that a space is defined by a different azimuth than 0 is very low
        azimuth = 0
        # this value should be set in relation to the Floor object
        if not self._boundary:
            raise ValueError(
                'You must call the `poly` method to create the boundary before calling '
                'this method.'
            )
        origin = self._boundary.geometry.lower_left_corner
        origin_pt = origin - floor_origin
        obj_lines = []
        obj_lines.append('"{}" = SPACE\n'.format(short_name(self.host.display_name)))
        obj_lines.append('   SHAPE           = POLYGON\n')
        obj_lines.append('   POLYGON         = "{} Plg"\n'.format(
            self.host.display_name))
        obj_lines.append('   AZIMUTH         = {}\n'.format(azimuth))
        obj_lines.append('   X               = {}\n'.format(origin_pt.x))
        obj_lines.append('   Y               = {}\n'.format(origin_pt.y))
        obj_lines.append('   Z               = {}\n'.format(origin_pt.z))
        obj_lines.append('   VOLUME          = {}\n'.format(self.host.volume))
        obj_lines.append('  ..\n')
        # obj_lines.append('   C-ACTIVITY-DESC = *{}*\n   ..\n'.format(str(obj.properties.energy.program_type)))
        spaces = ''.join(obj_lines)
        walls = '\n'.join([w.to_inp(origin) for w in self.walls])
        roofs = '\n'.join([r.to_inp(origin) for r in self.roofs])
        ground_floors = '\n'.join(
            [g.to_inp(origin) for g in self.ground_contact_surfaces]
        )
        exposed_floors = '\n'.join(
            [ef.to_inp(origin) for ef in self.exposed_floor_surfaces]
        )
        interior_floors = '\n'.join(
            [inf.to_inp(origin) for inf in self.interior_floor_surfaces]
        )
        adiabatic_floors = '\n'.join(
            [af.to_inp(origin) for af in self.adiabatic_floor_surfaces]
        )
        adiabatic_roofs = '\n'.join(
            [ar.to_inp(origin) for ar in self.adiabatic_roofs]
        )
        return '\n'.join(
            [spaces, walls, roofs, adiabatic_roofs, ground_floors, exposed_floors,
             interior_floors, adiabatic_floors])
