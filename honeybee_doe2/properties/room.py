# -*- coding: utf-8 -*-
from enum import Enum
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


class ZoneType(Enum):

    CONDITIONED = 'CONDITIONED'
    """Space is heated and/or cooled."""
    UNCONDITIONED = 'UNCONDITIONED'
    """Space is neither heated nor cooled."""
    PLENUM = 'PLENUM'
    """Space is a return air plenum."""


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
        if _boundary.has_holes:
            print(
                f'{self.host.display_name} has {len(_boundary.holes)} holes.'
                ' They will be removed.')
        _boundary._holes = []  # remove holes
        _boundary = _boundary.remove_colinear_vertices(tolerance=tol)
        _boundary = _boundary.remove_duplicate_vertices(tolerance=tol)
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
    def space_energy_properties(self):
        return self._convert_energy_properties(self.host)

    @staticmethod
    def _convert_energy_properties(host: Room) -> List[str]:
        doe_energy_properties = []
        if host.properties.energy.is_conditioned:
            doe_energy_properties.append(
                f'   ZONE-TYPE = {ZoneType.CONDITIONED.value}\n')
        else:
            doe_energy_properties.append(
                f'   ZONE-TYPE = {ZoneType.UNCONDITIONED.value}\n')
        if host.properties.energy.people:
            doe_energy_properties.append(
                f'   NUMBER-OF-PEOPLE = {host.properties.energy.people.people_per_area*host.floor_area}\n'
            )
            doe_energy_properties.append(
                f'   PEOPLE-SCHEDULE = "{short_name(host.properties.energy.people.occupancy_schedule.display_name)}_"\n'
            )

        if host.properties.energy.lighting:
            doe_energy_properties.append(
                f'   LIGHTING-W/AREA = {host.properties.energy.lighting.watts_per_area}\n'
            )
            doe_energy_properties.append(
                f'   LIGHTING-SCHEDULE = "{short_name(host.properties.energy.lighting.schedule.display_name)}_"\n'
            )

        if host.properties.energy.electric_equipment:
            doe_energy_properties.append(
                f'   EQUIP-SCHEDULE = ("{short_name(host.properties.energy.electric_equipment.schedule.display_name)}_")\n'
            )
            doe_energy_properties.append(
                f'   EQUIPMENT-W/AREA = {host.properties.energy.electric_equipment.watts_per_area}\n'
            )

            doe_energy_properties.append(
                f'   EQUIP-SENSIBLE = {1 - host.properties.energy.electric_equipment.lost_fraction - host.properties.energy.electric_equipment.latent_fraction}\n'
            )
            doe_energy_properties.append(
                f'   EQUIP-RAD-FRAC = {host.properties.energy.electric_equipment.radiant_fraction}\n'
            )
            doe_energy_properties.append(
                f'   EQUIP-LATENT = {host.properties.energy.electric_equipment.latent_fraction}\n'
            )

        if host.properties.energy.infiltration:
            doe_energy_properties.append(
                f'   INF-SCHEDULE = "{short_name(host.properties.energy.infiltration.schedule.display_name)}_"\n'
            )
            doe_energy_properties.append('   INF-METHOD = AIR-CHANGE\n')
            doe_energy_properties.append(
                f'   INF-FLOW/AREA = {host.properties.energy.infiltration.flow_per_exterior_area}\n'
            )

        return doe_energy_properties

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
        for prop in self.space_energy_properties:
            obj_lines.append(prop)
        obj_lines.append('  ..\n')

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
