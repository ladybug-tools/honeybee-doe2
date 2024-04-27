# coding=utf-8
"""Methods for grouping rooms to comply with INP rules."""
from __future__ import division
import math

from ladybug_geometry.geometry2d import Point2D, Polygon2D
from ladybug_geometry.geometry3d import Vector3D
from honeybee.typing import clean_doe2_string
from honeybee.room import Room

from .config import DOE2_TOLERANCE, FLOOR_LEVEL_TOL, RES_CHARS


def group_rooms_by_doe2_level(rooms, model_tolerance):
    """Group Honeybee Rooms according to acceptable floor levels in DOE-2.

    This means that not only will Rooms be on separate DOE-2 levels if their floor
    heights differ but also Rooms that share the same floor height but are
    disconnected from one another in plan will also be separate levels.
    For example, when the model is of two towers on a plinth, each tower will
    get its own separate level group.

    Args:
        rooms: A list of Honeybee Rooms to be grouped.
        model_tolerance: The tolerance of the model that the Rooms originated from.

    Returns:
        A tuple with three elements.

        -   room_groups: A list of lists where each sub-list contains Honeybee
            Rooms that should be on the same DOE-2 level.

        -   level_geometries: A list of Face3D with the same length as the
            room_groups, which contains the geometry that represents each floor
            level. These geometries will always be pointing upwards so that
            their vertices are counter-clockwise when viewed from above. They
            will also have colinear vertices removed such that they are ready
            to be translated to INP POLYGONS.
        
        -   level_names: A list of text strings that align with the level
            geometry and contain suggested names for the DOE-2 levels.
    """
    # set up lists of the outputs to be populated
    room_groups, level_geometries, level_names = [], [], []

    # first group the rooms by floor height
    grouped_rooms, _ = Room.group_by_floor_height(rooms, FLOOR_LEVEL_TOL)
    for fi, room_group in enumerate(grouped_rooms):
        # then, group the rooms by contiguous horizontal boundary
        hor_bounds = Room.grouped_horizontal_boundary(
            room_group, tolerance=model_tolerance, floors_only=True)
        if len(hor_bounds) == 0:  # possible when Rooms have no floors
            hor_bounds = Room.grouped_horizontal_boundary(
                room_group, tolerance=model_tolerance, floors_only=False)

        # if we got lucky and everything is one contiguous polygon, we're done!
        if len(hor_bounds) == 1:
            flr_geo = hor_bounds[0]
            flr_geo = flr_geo if flr_geo.normal.z >= 0 else flr_geo.flip()
            flr_geo = flr_geo.remove_colinear_vertices(tolerance=DOE2_TOLERANCE)
            room_groups.append(room_group)
            level_geometries.append(flr_geo)
            level_names.append('Level_{}'.format(fi))
        else:  # otherwise, we need to figure out which Room belongs to which geometry
            # first get a set of Point2Ds that are inside each room in plan
            room_pts, z_axis = [], Vector3D(0, 0, 1)
            for room in rooms:
                for face in room.faces:
                    if math.degrees(z_axis.angle(face.normal)) >= 91:
                        down_geo = face.geometry
                        break
                room_pt3d = down_geo.center if down_geo.is_convex else \
                    down_geo.pole_of_inaccessibility(DOE2_TOLERANCE)
                room_pts.append(Point2D(room_pt3d.x, room_pt3d.y))
            # loop through floor geometries and determine all rooms associated with them
            for si, flr_geo in enumerate(hor_bounds):
                flr_geo = flr_geo if flr_geo.normal.z >= 0 else flr_geo.flip()
                flr_geo = flr_geo.remove_colinear_vertices(tolerance=DOE2_TOLERANCE)
                flr_poly = Polygon2D([Point2D(pt.x, pt.y) for pt in flr_geo.boundary])
                flr_rooms = []
                for room, room_pt in zip(rooms, room_pts):
                    if flr_poly.is_point_inside_bound_rect(room_pt):
                        flr_rooms.append(room)
                room_groups.append(flr_rooms)
                level_geometries.append(flr_geo)
                level_names.append('Level_{}_Section{}'.format(fi, si))

    # return all of the outputs
    return room_groups, level_geometries, level_names


def group_rooms_by_doe2_hvac(model, hvac_mapping):
    """Group Honeybee Rooms according to HVAC logic.

    Args:
        model: A Honeybee Model for which Rooms will be grouped for HVAC assignment.
        hvac_mapping: Text to indicate how HVAC systems should be assigned.
            Model will use only one HVAC system for the whole model and
            AssignedHVAC will follow how the HVAC systems have been assigned
            to the Rooms.properties.energy.hvac. Choose from the options below.

            * Room
            * Model
            * AssignedHVAC

    Returns:
        A tuple with three elements.

        -   room_groups: A list of lists where each sub-list contains Honeybee
            Rooms that should ave the same HVAC system.
        
        -   hvac_names: A list of text strings that align with the room_groups
            and contain suggested names for the DOE-2 HVAC systems.
    """
    # clean up the hvac_mapping text
    hvac_mapping = hvac_mapping.upper().replace('-', '').replace(' ', '')

    # determine the mapping to be used
    if hvac_mapping == 'MODEL':
        hvac_name = clean_doe2_string('{}_Sys'.format(model.display_name), RES_CHARS)
        return [model.rooms], [hvac_name]
    elif hvac_mapping == 'ROOM':
        hvac_names = [clean_doe2_string('{}_Sys'.format(room.display_name), RES_CHARS)
                      for room in model.rooms]
        room_groups = [[room] for room in model.rooms]
    else:  # assume that it is the assigned HVAC
        hvac_dict = {}
        for room in model.rooms:
            if room.properties.energy.hvac is not None:
                hvac_id = room.properties.energy.hvac.display_name
                try:
                    hvac_dict[hvac_id].append(room)
                except KeyError:  # the first time that we are encountering the HVAC
                    hvac_dict[hvac_id] = [room]
            else:
                try:
                    hvac_dict['Unassigned'].append(room)
                except KeyError:  # the first time that we have an unassigned room
                    hvac_dict['Unassigned'] = [room]
        room_groups, hvac_names = [], []
        for hvac_name, rooms in hvac_dict.items():
            room_groups.append(rooms)
            hvac_names.append(clean_doe2_string(hvac_name, RES_CHARS))

    return room_groups, hvac_names
