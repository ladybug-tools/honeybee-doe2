# coding=utf-8
"""Methods to write to inp."""
from __future__ import division
import math

from ladybug_geometry.geometry2d import Point2D
from ladybug_geometry.geometry3d import Vector3D, Point3D, Plane, Face3D
from honeybee.typing import clean_doe2_string
from honeybee.boundarycondition import Surface
from honeybee.facetype import Wall, Floor, RoofCeiling
from honeybee.room import Room
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.air import AirBoundaryConstruction
from honeybee_energy.lib.constructionsets import generic_construction_set

from .config import DOE2_TOLERANCE, DOE2_ANGLE_TOL, FLOOR_LEVEL_TOL, RECT_WIN_SUBD, \
    DOE2_INTERIOR_BCS, GEO_CHARS, RES_CHARS
from .util import generate_inp_string, header_comment_minor, \
    header_comment_major
from .construction import opaque_material_to_inp, opaque_construction_to_inp, \
    window_construction_to_inp, door_construction_to_inp, air_construction_to_inp
from .schedule import energy_trans_sch_to_transmittance
from .load import people_to_inp, lighting_to_inp, equipment_to_inp, \
    infiltration_to_inp
from .simulation import SimulationPar


def face_3d_to_inp(face_3d, parent_name='HB object'):
    """Convert a Face3D into a DOE-2 POLYGON string and info to position it in space.

    In this operation, all holes in the Face3D are ignored since they are not
    supported by DOE-2. Collapsing the boundary and holes into a single list
    that winds inward to cut out the holes will cause eQuest to raise an error.

    Args:
        face_3d: A ladybug-geometry Face3D object for which a INP POLYGON
            string will be generated.
        parent_name: The name of the parent object that will reference this
            POLYGON. This will be used to generate a name for the polygon.
            Note that this should ideally have 24 characters or less so that
            the result complies with the strict 32 character limit of DOE-2
            identifiers.

    Returns:
        A tuple with two elements.

        -   polygon_str: Text string for the INP polygon.

        -   position_info: A tuple of values used to locate the Polygon in 3D space.
            The order of properties in the tuple is as follows: (ORIGIN, TILT, AZIMUTH).
    """
    # TODO: Consider adding a workaround for the DOE-2 limit of 40 vertices
    # perhaps we can just say NO-SHAPE and specify AREA, VOLUME, and HEIGHT
    # get the main properties that place the geometry in 3D space
    pts_3d = face_3d.lower_left_counter_clockwise_boundary
    llc_origin = pts_3d[0]
    tilt, azimuth = math.degrees(face_3d.tilt), math.degrees(face_3d.azimuth)

    # get the 2D vertices in the plane of the Face
    if DOE2_ANGLE_TOL <= tilt <=  180 - DOE2_ANGLE_TOL:  # vertical or tilted
        proj_y = Vector3D(0, 0, 1).project(face_3d.normal)
        proj_x = proj_y.rotate(face_3d.normal, math.pi / -2)
        ref_plane = Plane(face_3d.normal, llc_origin, proj_x)
        vertices = [ref_plane.xyz_to_xy(pt) for pt in pts_3d]
    else:  # horizontal; ensure vertices are always counterclockwise from above
        llc = Point2D(llc_origin.x, llc_origin.y)
        vertices = [Point2D(v[0] - llc.x, v[1] - llc.y) for v in pts_3d]
        if tilt > 180 - DOE2_ANGLE_TOL:
            vertices = [Point2D(v.x, -v.y) for v in vertices]

    # format the vertices into a POLYGON string
    vert_template = '( %f, %f )'
    verts_values = tuple(vert_template % (pt.x, pt.y) for pt in vertices)
    verts_keywords = tuple('V{}'.format(i + 1) for i in range(len(verts_values)))
    poly_name = '{} Plg'.format(parent_name)
    polygon_str = generate_inp_string(poly_name, 'POLYGON', verts_keywords, verts_values)
    position_info = (llc_origin, azimuth, tilt)
    return polygon_str, position_info


def shade_mesh_to_inp(shade_mesh):
    """Generate an INP string representation of a ShadeMesh.

    Args:
        shade_mesh: A honeybee ShadeMesh for which an INP representation
            will be returned.
        
    Returns:
        A tuple with two elements.

        -   shade_polygons: A list of text strings for the INP polygons needed
            to represent the ShadeMesh.

        -   shade_defs: A list of text strings for the INP definitions needed
            to represent the ShadeMesh.
    """
    # TODO: Sense when the shade is a rectangle and, if so, translate it without POLYGON
    # set up collector lists and properties for all shades
    shade_type = 'FIXED-SHADE' if shade_mesh.is_detached else 'BUILDING-SHADE'
    base_id = clean_doe2_string(shade_mesh.identifier, GEO_CHARS)
    trans = energy_trans_sch_to_transmittance(shade_mesh)
    keywords = ('SHAPE', 'POLYGON', 'TRANSMITTANCE',
                'X-REF', 'Y-REF', 'Z-REF', 'TILT', 'AZIMUTH')
    shade_polygons, shade_defs = [], []
    # loop through the mesh faces and create individual shade objects
    for i, face in enumerate(shade_mesh.geometry.face_vertices):
        f_geo = Face3D(face)
        shd_geo = f_geo.geometry if f_geo.altitude > 0 else f_geo.geometry.flip()
        doe2_id = '{}{}'.format(base_id, i)
        shade_polygon, pos_info = face_3d_to_inp(shd_geo, doe2_id)
        origin, tilt, az = pos_info
        values = ('POLYGON', '"{} Plg"', trans, origin.x, origin.y, origin.z, tilt, az)
        shade_def = generate_inp_string(doe2_id, shade_type, keywords, values)
        shade_polygons.append(shade_polygon)
        shade_defs.append(shade_def)
    return shade_polygons, shade_defs


def shade_to_inp(shade):
    """Generate an INP string representation of a Shade.

    Args:
        shade: A honeybee Shade for which an INP representation will be returned.

    Returns:
        A tuple with two elements.

        -   shade_polygon: Text string for the INP polygon for the Shade.

        -   shade_def: Text string for the INP definition of the Shade.
    """
    # TODO: Sense when the shade is a rectangle and, if so, translate it without POLYGON
    # create the polygon string from the geometry
    shade_type = 'FIXED-SHADE' if shade.is_detached else 'BUILDING-SHADE'
    doe2_id = clean_doe2_string(shade.identifier, GEO_CHARS)
    shd_geo = shade.geometry if shade.altitude > 0 else shade.geometry.flip()
    clean_geo = shd_geo.remove_colinear_vertices(DOE2_TOLERANCE)
    shade_polygon, pos_info = face_3d_to_inp(clean_geo, doe2_id)
    origin, tilt, az = pos_info
    # create the shade definition, which includes the position information
    trans = energy_trans_sch_to_transmittance(shade)
    keywords = ('SHAPE', 'POLYGON', 'TRANSMITTANCE',
                'X-REF', 'Y-REF', 'Z-REF', 'TILT', 'AZIMUTH')
    values = ('POLYGON', '"{} Plg"', trans,
              origin.x, origin.y, origin.z, tilt, az)
    shade_def = generate_inp_string(doe2_id, shade_type, keywords, values)
    return shade_polygon, shade_def


def door_to_inp(door):
    """Generate an INP string representation of a Door.

    Doors assigned to a parent Face will use the parent Face plane in order to
    determine their XY coordinates. Otherwise, the Door's own plane will be used.

    Note that the resulting string does not include full construction definitions.
    Also note that shades assigned to the Door are not included in the resulting
    string. To write these objects into a final string, you must loop through the
    Door.shades, and call the to.inp method on each one.

    Args:
        door: A honeybee Door for which an INP representation will be returned.

    Returns:
        Text string for the INP definition of the Door.
    """
    # extract the plane information from the parent geometry
    if door.has_parent:
        parent_llc = door.parent.geometry.lower_left_corner
        rel_plane = door.parent.geometry.plane
    else:
        parent_llc = door.geometry.lower_left_corner
        rel_plane = door.geometry.plane
    # get the LLC and URC of the bounding rectangle of the door
    apt_llc = door.geometry.lower_left_corner
    apt_urc = door.geometry.upper_right_corner

    # determine the width and height and origin in the parent coordinate system
    if DOE2_ANGLE_TOL <= door.tilt <=  180 - DOE2_ANGLE_TOL:  # vertical or tilted
        proj_y = Vector3D(0, 0, 1).project(rel_plane.n)
        proj_x = proj_y.rotate(rel_plane.n, math.pi / -2)
    else:  # located within the XY plane
        proj_x = Vector3D(1, 0, 0)
    ref_plane = Plane(rel_plane.n, parent_llc, proj_x)
    min_2d = ref_plane.xyz_to_xy(apt_llc)
    max_2d = ref_plane.xyz_to_xy(apt_urc)
    width = max_2d.x - min_2d.x
    height = max_2d.y - min_2d.y

    # create the aperture definition
    doe2_id = clean_doe2_string(door.identifier, GEO_CHARS)
    constr_o_name = door.properties.energy.construction.identifier
    constr = clean_doe2_string(constr_o_name, RES_CHARS)
    keywords = ('X', 'Y', 'WIDTH', 'HEIGHT', 'CONSTRUCTION')
    values = (min_2d.x, min_2d.y, width, height, constr)
    door_def = generate_inp_string(doe2_id, 'DOOR', keywords, values)
    return door_def


def aperture_to_inp(aperture):
    """Generate an INP string representation of a Aperture.

    Apertures assigned to a parent Face will use the parent Face plane in order to
    determine their XY coordinates. Otherwise, the Aperture's own plane will be used.

    Note that the resulting string does not include full construction definitions.
    Also note that shades assigned to the Aperture are not included in the resulting
    string. To write these objects into a final string, you must loop through the
    Aperture.shades, and call the to.inp method on each one.

    Args:
        aperture: A honeybee Aperture for which an INP representation will be returned.

    Returns:
        Text string for the INP definition of the Aperture.
    """
    # extract the plane information from the parent geometry
    if aperture.has_parent:
        parent_llc = aperture.parent.geometry.lower_left_corner
        rel_plane = aperture.parent.geometry.plane
    else:
        parent_llc = aperture.geometry.lower_left_corner
        rel_plane = aperture.geometry.plane
    # get the LLC and URC of the bounding rectangle of the aperture
    apt_llc = aperture.geometry.lower_left_corner
    apt_urc = aperture.geometry.upper_right_corner

    # determine the width and height and origin in the parent coordinate system
    if DOE2_ANGLE_TOL <= aperture.tilt <=  180 - DOE2_ANGLE_TOL:  # vertical or tilted
        proj_y = Vector3D(0, 0, 1).project(rel_plane.n)
        proj_x = proj_y.rotate(rel_plane.n, math.pi / -2)
    else:  # located within the XY plane
        proj_x = Vector3D(1, 0, 0)
    ref_plane = Plane(rel_plane.n, parent_llc, proj_x)
    min_2d = ref_plane.xyz_to_xy(apt_llc)
    max_2d = ref_plane.xyz_to_xy(apt_urc)
    width = max_2d.x - min_2d.x
    height = max_2d.y - min_2d.y

    # create the aperture definition
    doe2_id = clean_doe2_string(aperture.identifier, GEO_CHARS)
    constr_o_name = aperture.properties.energy.construction.identifier
    constr = clean_doe2_string(constr_o_name, RES_CHARS)
    keywords = ('X', 'Y', 'WIDTH', 'HEIGHT', 'GLASS-TYPE')
    values = (min_2d.x, min_2d.y, width, height, constr)
    aperture_def = generate_inp_string(doe2_id, 'WINDOW', keywords, values)
    return aperture_def


def face_to_inp(face, space_origin=Point3D(0, 0, 0)):
    """Generate an INP string representation of a Face.

    Note that the resulting string does not include full construction definitions.

    Also note that this does not include any of the shades assigned to the Face
    in the resulting string. Nor does it include the strings for the
    apertures or doors. To write these objects into a final string, you must
    loop through the Face.apertures, and Face.doors and call the to.inp method
    on each one.

    Args:
        face: A honeybee Face for which an INP representation will be returned.
        space_origin: A ladybug-geometry Point3D for the origin of the space
            to which the Face is assigned. (Default: (0, 0, 0)).
    
    Returns:
        A tuple with two elements.

        -   face_polygon: Text string for the INP polygon for the Face.

        -   face_def: Text string for the INP definition of the Face.
    """
    # set up attributes based on the face type and boundary condition
    f_type_str, bc_str = str(face.type), str(face.boundary_condition)
    if bc_str == 'Outdoors':
        doe2_type = 'EXTERIOR-WALL'  # DOE2 uses walls for a lot of things
        if f_type_str == 'RoofCeiling':
            doe2_type = 'ROOF'
    elif bc_str in DOE2_INTERIOR_BCS or f_type_str == 'AirBoundary':
        doe2_type = 'INTERIOR-WALL'  # DOE2 uses walls for a lot of things
    else:  # likely ground or some other fancy ground boundary condition
        doe2_type = 'UNDERGROUND-WALL'

    # create the polygon string from the geometry
    doe2_id = clean_doe2_string(face.identifier, GEO_CHARS)
    f_geo = face.geometry.remove_colinear_vertices(DOE2_TOLERANCE)
    face_polygon, pos_info = face_3d_to_inp(f_geo, doe2_id)
    face_origin, tilt, az = pos_info
    origin = face_origin - space_origin

    # create the face definition, which includes the position info
    constr_o_name = face.properties.energy.construction.identifier
    constr = clean_doe2_string(constr_o_name, RES_CHARS)
    keywords = ['POLYGON', 'CONSTRUCTION', 'TILT', 'AZIMUTH', 'X', 'Y', 'Z']
    values = ['"{} Plg"'.format(doe2_id), constr, tilt, az, origin.x, origin.y, origin.z]
    if bc_str == 'Surface':
        adj_room = face.boundary_condition.boundary_condition_objects[-1]
        adj_id = clean_doe2_string(adj_room, GEO_CHARS)
        values.append('"{}"'.format(adj_id))
        keywords.append('NEXT-TO')
    elif doe2_type == 'INTERIOR-WALL':  # assume that it is adiabatic
        keywords.append('INT-WALL-TYPE')
        values.append('ADIABATIC')
    if f_type_str == 'Floor' and doe2_type != 'INTERIOR-WALL':
        keywords.append('LOCATION')
        values.append('BOTTOM')
    face_def = generate_inp_string(doe2_id, doe2_type, keywords, values)

    return face_polygon, face_def


def room_to_inp(room, floor_origin=Point3D(0, 0, 0), exclude_interior_walls=False,
                exclude_interior_ceilings=False):
    """Generate an INP string representation of a Room.

    This will include the Room's constituent Faces, Apertures and Doors with
    each of these elements being a separate item in the list of strings returned.
    However, any shades assigned to the Room or its constituent elements are
    excluded and should be written by looping through the shades on the parent model.

    The resulting string will also include all internal gain definitions for the
    Room (people, lights, equipment), infiltration definitions, ventilation
    requirements, and thermostat objects.
    
    However, complete schedule definitions assigned to these load objects are
    excluded as well as any construction or material definitions.

    Args:
        floor_origin: A ladybug-geometry Point3D for the origin of the
            floor (aka. story) to which the Room is a part of. (Default: (0, 0, 0)).
        exclude_interior_walls: Boolean to note whether interior wall Faces
            should be excluded from the resulting string. (Default: False).
        exclude_interior_ceilings: Boolean to note whether interior ceiling
            Faces should be excluded from the resulting string. (Default: False).

    Returns:
        A tuple with two elements.

        -   room_polygons: A list of text strings for the INP polygons needed
            to represent the Room and all of its constituent Faces.

        -   room_defs: A list of text strings for the INP definitions needed
            to represent the Room and all of its constituent Faces, Apertures
            and Doors.
    """
    # TODO: Sense when a Room is an extruded floor plate and, if so, do not use
    # POLYGON to describe the Room faces

    # set up attributes based on the Room's energy properties
    energy_attr_keywords = ['ZONE-TYPE']
    if room.exclude_floor_area:
        energy_attr_values = ['PLENUM']
    elif room.properties.energy.is_conditioned:
        energy_attr_values = ['CONDITIONED']
    else:
        energy_attr_values = ['UNCONDITIONED']
    if room.properties.energy.people:
        ppl_kwd, ppl_val = people_to_inp(room)
        energy_attr_keywords.extend(ppl_kwd)
        energy_attr_values.extend(ppl_val)
    if room.properties.energy.lighting:
        lgt_kwd, lgt_val = lighting_to_inp(room)
        energy_attr_keywords.extend(lgt_kwd)
        energy_attr_values.extend(lgt_val)
    if room.properties.energy.electric_equipment or room.properties.energy.gas_equipment:
        eq_kwd, eq_val = equipment_to_inp(room)
        energy_attr_keywords.extend(eq_kwd)
        energy_attr_values.extend(eq_val)
    if room.properties.energy.infiltration:
        inf_kwd, inf_val = infiltration_to_inp(room)
        energy_attr_keywords.extend(inf_kwd)
        energy_attr_values.extend(inf_val)

    # create the polygon string from the geometry
    doe2_id = clean_doe2_string(room.identifier, GEO_CHARS)
    r_geo = room.horizontal_boundary(match_walls=False, tolerance=DOE2_TOLERANCE)
    r_geo = r_geo if r_geo.normal.z >= 0 else r_geo.flip()
    r_geo = r_geo.remove_colinear_vertices(tolerance=DOE2_TOLERANCE)
    room_polygon, pos_info = face_3d_to_inp(r_geo, doe2_id)
    space_origin, _, _ = pos_info
    origin = space_origin - floor_origin

    # create the space definition, which includes the position info
    keywords = ['SHAPE', 'POLYGON', 'AZIMUTH', 'X', 'Y', 'Z' 'VOLUME']
    values = ['POLYGON', '"{} Plg"'.format(doe2_id), 0,
              origin.x, origin.y, origin.z, room.volume]
    if room.multiplier != 1:
        keywords.append('MULTIPLIER')
        values.append(room.multiplier)
    keywords.extend(energy_attr_keywords)
    values.extend(energy_attr_values)
    space_def = generate_inp_string(doe2_id, 'SPACE', keywords, values)

    # gather together all definitions and polygons to define the room
    room_polygons = [room_polygon]
    room_defs = [space_def]
    for face in room.faces:
        # first check if this is a face that should be excluded
        if isinstance(face.boundary_condition, Surface):
            if exclude_interior_walls and isinstance(face.type, Wall):
                continue
            elif exclude_interior_ceilings and isinstance(face.type, (Floor, RoofCeiling)):
                continue
        # add the face definition along with all apertures and doors
        face_polygon, face_def = face_to_inp(face, space_origin)
        room_polygons.append(face_polygon)
        room_defs.append(face_def)
        for ap in face.apertures:
            ap_def = aperture_to_inp(ap)
            room_defs.append(ap_def)
        if not isinstance(face.boundary_condition, Surface):
            for dr in face.doors:
                dr_def = door_to_inp(dr)
                room_defs.append(dr_def)
    return room_polygons, room_defs


def model_to_inp(
    model, simulation_par=None, hvac_mapping='Story',
    exclude_interior_walls=False, exclude_interior_ceilings=False
):
    """Generate an INP string representation of a Model.

    The resulting string will include all geometry (Rooms, Faces, Apertures,
    Doors, Shades), all fully-detailed constructions + materials, all fully-detailed
    schedules, and the room properties. It will also include the simulation
    parameters. Essentially, the string includes everything needed to simulate
    the model.

    Args:
        model: A honeybee Model for which an INP representation will be returned.
        simulation_par: A honeybee-doe2 SimulationPar object to specify how the
            DOE-2 simulation should be run. If None, default simulation
            parameters will be generated, which will run the simulation for the
            full year. (Default: None).
        hvac_mapping: Text to indicate how HVAC systems should be assigned to the
            exported model. Story will assign one HVAC system for each distinct
            level polygon, Model will use only one HVAC system for the whole model
            and AssignedHVAC will follow how the HVAC systems have been assigned
            to the Rooms.properties.energy.hvac. Choose from the options
            below. (Default: Story).

            * Room
            * Story
            * Model
            * AssignedHVAC

        exclude_interior_walls: Boolean to note whether interior wall Faces
            should be excluded from the resulting string. (Default: False).
        exclude_interior_ceilings: Boolean to note whether interior ceiling
            Faces should be excluded from the resulting string. (Default: False).

    Usage:

    .. code-block:: python

        import os
        from ladybug.futil import write_to_file
        from honeybee.model import Model
        from honeybee.room import Room
        from honeybee.config import folders

        # Crate an input Model
        room = Room.from_box('Tiny House Zone', 5, 10, 3)
        room.properties.energy.program_type = office_program
        room.properties.energy.add_default_ideal_air()
        model = Model('Tiny House', [room])

        # create the INP string for the model
        inp_str = model.to.inp(model)

        # write the final string into an INP
        inp = os.path.join(folders.default_simulation_folder, 'test_file', 'in.inp')
        write_to_file(inp, inp_str, True)
    """
    # duplicate model to avoid mutating it as we edit it for INP export
    original_model = model
    model = model.duplicate()
    # scale the model if the units are not feet
    if model.units != 'Feet':
        model.convert_to_units('Feet')
    tol = model.tolerance
    # remove degenerate geometry within native DOE-2 tolerance
    try:
        model.remove_degenerate_geometry(DOE2_TOLERANCE)
    except ValueError:
        error = 'Failed to remove degenerate Rooms.\nYour Model units system is: {}. ' \
            'Is this correct?'.format(original_model.units)
        raise ValueError(error)
    # convert all of the Aperture geometries to rectangles so they can be translated
    model.rectangularize_apertures(
        subdivision_distance=RECT_WIN_SUBD, max_separation=0.0,
        merge_all=True, resolve_adjacency=True
    )
    # reset identifiers to make them unique and derived from the display names
    model.reset_ids()

    # write the simulation parameters into the string
    model_str = ['INPUT ..\n\n']
    sim_par = simulation_par if simulation_par is not None else SimulationPar()
    model_str.append(sim_par.to_inp())

    # write all of the schedules
    all_day_scheds, all_week_scheds, all_year_scheds = [], [], []
    used_day_sched_ids, used_day_count = {}, 1
    all_scheds = model.properties.energy.schedules
    for sched in all_scheds:
        if sched.__class__.__name__ == 'ScheduleRuleset':
            year_schedule, week_schedules = sched.to_inp()
            # check that day schedules aren't referenced by other model schedules
            day_scheds = []
            for day in sched.day_schedules:
                if day.identifier not in used_day_sched_ids:
                    day_scheds.append(day.to_inp(sched.schedule_type_limit))
                    used_day_sched_ids[day.identifier] = day
                elif day != used_day_sched_ids[day.identifier]:
                    new_day = day.duplicate()
                    new_day.identifier = 'Schedule Day {}'.format(used_day_count)
                    day_scheds.append(new_day.to_inp(sched.schedule_type_limit))
                    for i, week_sch in enumerate(week_schedules):
                        old_day_id = clean_doe2_string(day.identifier, RES_CHARS)
                        new_day_id = clean_doe2_string(new_day.identifier, RES_CHARS)
                        week_schedules[i] = week_sch.replace(old_day_id, new_day_id)
                    used_day_count += 1
            all_day_scheds.extend(day_scheds)
            all_week_scheds.extend(week_schedules)
            all_year_scheds.append(year_schedule)
        else:  # ScheduleFixedInterval
            pass
            # TODO: Add translators for ScheduleFixedInterval
    model_str.append(header_comment_minor('Day Schedules'))
    model_str.extend(all_day_scheds)
    model_str.append(header_comment_minor('Week Schedules'))
    model_str.extend(all_week_scheds)
    model_str.append(header_comment_minor('Annual Schedules'))
    model_str.extend(all_year_scheds)

    # write all of the materials and constructions
    window_constructions = model.properties.energy.aperture_constructions()
    door_constructions = model.properties.energy.door_constructions()
    drc_ids = set([con.identifier for con in door_constructions])
    materials = []
    construction_strs = []
    all_constrs = model.properties.energy.constructions + \
        generic_construction_set.constructions_unique
    for constr in set(all_constrs):
        if isinstance(constr, OpaqueConstruction) and constr.identifier not in drc_ids:
            materials.extend(constr.materials)
            construction_strs.append(opaque_construction_to_inp(constr))
        elif isinstance(constr, AirBoundaryConstruction):
            construction_strs.append(air_construction_to_inp(constr))
    model_str.append(header_comment_minor('Materials / Layers / Constructions'))
    model_str.extend([opaque_material_to_inp(mat) for mat in set(materials)])
    model_str.extend(construction_strs)
    model_str.append(header_comment_minor('Glass Types'))
    for w_con in window_constructions:
        model_str.append(window_construction_to_inp(w_con))
    model_str.append(header_comment_minor('Door Construction'))
    for dr_con in door_constructions:
        model_str.append(door_construction_to_inp(dr_con))

    # loop through rooms grouped by floor level and boundary to get polygons
    room_polygons, bldg_geo_defs = [], []
    
    
    
    model_str.append(header_comment_minor('Polygons'))
    model_str.append(header_comment_minor('Wall Parameters'))
    model_str.append(header_comment_minor('Fixed and Building Shades'))
    model_str.append(header_comment_minor('Misc Cost Related Objects'))
    model_str.append(header_comment_major('Performance Curves'))
    model_str.append(header_comment_major('Floors / Spaces / Walls / Windows / Doors'))

    # assign HVAC systems given the specified hvac_mapping
    model_str.append(header_comment_major('Electric & Fuel Meters'))
    for meter in ('Electric Meters', 'Fuel Meters', 'Master Meters'):
        model_str.append(header_comment_minor(meter))
    model_str.append(header_comment_major('HVAC Circulation Loops / Plant Equipment'))
    hvac_comp_types = (
        'Pumps', 'Heat Exchangers', 'Circulation Loops', 'Chillers', 'Boilers',
        'Domestic Water Heaters', 'Heat Rejection', 'Tower Free Cooling',
        'Photovoltaic Modules', 'Electric Generators', 'Thermal Storage',
        'Ground Loop Heat Exchangers', 'Compliance DHW (residential dwelling units)')
    for comp in hvac_comp_types:
        model_str.append(header_comment_minor(comp))
    model_str.append(header_comment_major('Steam & Chilled Water Meters'))
    model_str.append(header_comment_minor('Steam Meters'))
    model_str.append(header_comment_minor('Chilled Water Meters'))
    model_str.append(header_comment_major('HVAC Systems / Zones'))


    # provide a few last comment headers and end the file
    model_str.append(header_comment_major('Metering & Misc HVAC'))
    model_str.append(header_comment_minor('Equipment Controls'))
    model_str.append(header_comment_minor('Load Management'))
    model_str.append(header_comment_major('Utility Rates'))
    for rate in ('Ratchets', 'Block Charges', 'Utility Rates'):
        model_str.append(header_comment_minor(rate))
    model_str.append(header_comment_major('Output Reporting'))
    report_types = (
        'Loads Non-Hourly Reporting', 'Systems Non-Hourly Reporting',
        'Plant Non-Hourly Reporting', 'Economics Non-Hourly Reporting',
        'Hourly Reporting', 'THE END')
    for report in report_types:
        model_str.append(header_comment_minor(report))
    model_str = ['END ..\nCOMPUTE ..\nSTOP ..\n']
    return '\n'.join(model_str)


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

        -   level_geometry: A list of Face3D with the same length as the
            room_groups, which contains the geometry that represents each floor
            level. These geometries will always be pointing upwards so that
            their vertices are counter-clockwise when viewed from above. They
            will also have colinear vertices removed such that they are ready
            to be translated to INP POLYGONS.
        
        -   level_names: A list of text strings that align with the level
            geometry and contain suggested names for the DOE-2 levels.
    """
    # set up lists of the outputs to be populated
    room_groups, level_geometry, level_names = [], [], []

    # first group the rooms by floor height
    grouped_rooms = Room.group_by_floor_height(rooms, FLOOR_LEVEL_TOL)
    for fi, room_group in enumerate(grouped_rooms):
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
            level_geometry.append(flr_geo)
            level_names.append('Level_{}'.format(fi))
        else:  # otherwise, we need to figure out which Room belongs to which geometry
            for flr_geo in hor_bounds:
                flr_geo = flr_geo if flr_geo.normal.z >= 0 else flr_geo.flip()
                r_geo = r_geo.remove_colinear_vertices(tolerance=DOE2_TOLERANCE)

    # return all of the outputs
    return room_groups, level_geometry, level_names
