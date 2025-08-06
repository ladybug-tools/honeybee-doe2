# coding=utf-8
"""Methods to read inp files to Honeybee."""
from __future__ import division

import os
import math
import re
from collections import defaultdict

from ladybug_geometry.geometry3d import Point3D, Vector3D, Face3D
from honeybee.model import Model
from honeybee.facetype import Wall, RoofCeiling, Floor
from honeybee.room import Room
from honeybee.face import Face
from honeybee.aperture import Aperture
from honeybee.door import Door
from honeybee_energy.boundarycondition import Adiabatic
from honeybee.boundarycondition import Outdoors, Ground
from honeybee.typing import clean_string

from .config import DOE2_ANGLE_TOL, DOE2_TOLERANCE
from .util import clean_inp_file_contents, doe2_object_blocks, parse_inp_string

_CMD_TO_BC = {
    'EXTERIOR-WALL':   Outdoors,
    'INTERIOR-WALL':   Adiabatic,
    'UNDERGROUND-WALL': Ground,
    'ROOF':            Outdoors,
}


def model_from_inp_file(inp_file):
    """Convert an inp file to an HBJSON Model object

    Args:
        inp_file: A text string for the path to an INP file.

    Returns:
        A honeybee Model object.
    """
    assert os.path.isfile(inp_file), 'No file was found at: {}'.format(inp_file)
    with open(inp_file, 'r') as doe_file:
        inp_content = doe_file.read()
    return model_from_inp(inp_content)


def model_from_inp(inp_file_contents):
    """Convert an inp file to an HBJSON Model object

    Args:
        inp_file_contents: A text string of the complete contents of an INP file.

    Returns:
        A honeybee Model object.
    """
    cmd_dict = command_dict_from_inp(inp_file_contents)
    floors = cmd_dict.get("FLOOR", {})
    polys = cmd_dict.get("POLYGON", {})
    glob_az = -float(cmd_dict.get("BUILD-PARAMETERS", {}).get("AZIMUTH", 0) or 0)

    if not floors:
        raise ValueError("No FLOOR objects found in INP - nothing to translate.")

    rooms = []

    for flr_name, flr in floors.items():
        fx, fy, fz, flr_az = _origin_and_azimuth(flr, None, False)
        flr_origin = Point3D(fx, fy, fz)
        floor_poly = (flr.get("POLYGON") or "").strip('"')
        floor_verts = _verts_to_tuples(polys.get(floor_poly, {}))
        flr_mult = (flr.get("MULTIPLIER") or 1.0)

        spaces = _child_objects_from_parent(cmd_dict, flr_name, "FLOOR", "SPACE")
        for spc_name, spc in spaces.items():
            shape = (spc.get("SHAPE") or "").upper()
            if not shape or shape == "NO-SHAPE":
                continue
            if shape == "BOX":
                # TODO: Support translation of BOX SHAPE SPACE objects.
                # Need to find or create INP example file for this
                msg = '{} is defined by a BOX - convert to POLYGON.'.format(spc_name)
                raise ValueError(msg)

            # Local footprint
            plg = spc.get("POLYGON", "").strip('"')
            spc_verts_local = _verts_to_tuples(polys.get(plg, {}))
            if not spc_verts_local:
                continue
            spc_pts_local = [Point3D(x, y, 0) for x, y in spc_verts_local]

            # Space transform
            sx, sy, sz, spc_az = _origin_and_azimuth(spc, floor_verts, False)
            spc_pts_global = _transform_space_points(
                spc_pts_local, Point3D(sx, sy, sz), spc_az,
                flr_origin, flr_az,
                glob_az
            )

            walls = _surfaces_from_space(cmd_dict, spc_name)
            detailed = walls and all(w.get("POLYGON") for w in walls.values())
            # for now, we only use detailed translator if all walls are POLYGON shape
            # TODO: support preservation of all face geometry when only some are POLYGON
            if detailed:
                faces = _volume_from_polygons(
                    cmd_dict,
                    walls,
                    polys,
                    spc_pts_global, spc_pts_local, spc_name,
                    flr_origin, flr_az, glob_az,
                )
            else:
                edge_info, floor_bc, ceiling_bc = \
                    _edge_info_map(cmd_dict, walls, spc_pts_global, spc_pts_local)
                faces = _extruded_shell(spc, spc_pts_global, edge_info,
                                        floor_bc, ceiling_bc, spc_name, flr)

            room = Room(identifier=clean_string(spc_name), faces=faces)
            room.display_name = spc_name
            room.story = flr_name
            room.multiplier = flr_mult
            rooms.append(room)

    model_name = cmd_dict.get('TITLE', {}).get('LINE-1', 'Model From DOE2')
    model_name = model_name.replace('*', '')

    return Model(clean_string(model_name), rooms, units='Feet',
                 tolerance=DOE2_TOLERANCE, angle_tolerance=DOE2_ANGLE_TOL)


def command_dict_from_inp(inp_file_contents):
    """Get a dictionary of INP commands and U-names from a INP file content string.

    Args:
        inp_file_contents: A text string of the complete contents of an INP file.

    Returns:
        A dictionary with all the DOE-2 attributes for each object
        converting keyword values to float when possible plus a "__line__"
        indicating its sequence in the file to be used to solve child/parent
        relationships {command: {u_name: {key: value, "__line__": line_number}}}
    """
    # clean the contents of the file and break it into blocks
    inp_file_contents = clean_inp_file_contents(inp_file_contents)
    blocks = doe2_object_blocks(inp_file_contents)
    global_parameters = {}
    result = defaultdict(dict)
    cmd_blocks = []
    block_line_count = 1

    # Get globals and TITLE first since they are formatted slightly differently
    for blk in blocks:
        u_name, cmd, keys, vals = parse_inp_string(blk)
        if cmd == 'PARAMETER':
            key, val_raw = keys[0], vals[0]
            try:
                global_parameters[key] = float(val_raw)
            except ValueError:
                global_parameters[key] = val_raw
        elif cmd == 'TITLE':
            key, val = keys[0], vals[0]
            result['TITLE'][key] = val
        else:
            cmd_blocks.append(blk)

    for blk in cmd_blocks:
        u_name, cmd, keys, vals = parse_inp_string(blk)

        if keys is None or vals is None:
            continue  # ignore the block if it does not have any keywords

        attr_d = {}
        for k, v in zip(keys, vals):
            try:
                attr_d[k] = float(v)
            except ValueError:
                attr_d[k] = v
        attr_d['__line__'] = block_line_count
        attr_d['cmd'] = cmd
        block_line_count += 1
        result[cmd][u_name] = attr_d

    if global_parameters:
        result['PARAMETER'] = global_parameters

    return dict(result)


def _volume_from_polygons(
    cmd_dict, walls, polys, spc_pts_global, spc_pts_local, spc_name,
    flr_origin, flr_az, glob_az
):
    """Build detailed faces when each wall has its own POLYGON.

    Args:
        cmd_dict: Command dictionary containing all DOE2 objects.
        walls: Dictionary of wall objects and their attributes.
        polys: Dictionary of polygon objects and their attributes.
        spc_pts_global: List of space points in global coordinates.
        spc_pts_local: List of space points in local coordinates.
        spc_name: Name of the space.
        flr_origin: Point3D object representing the floor origin.
        flr_az: Floor azimuth angle in degrees.
        glob_az: Global azimuth angle in degrees.

    Returns:
        list[Face]: A list of honeybee Face objects representing the space geometry,
        including walls, floor, and ceiling with their respective apertures and doors.
    """
    faces = []
    idx = 1

    base_z = spc_pts_global[0].z if spc_pts_global else 0

    for w_name, w_attrs in walls.items():
        plg = (w_attrs.get('POLYGON') or '').strip('"')
        verts_local = _verts_to_tuples(polys.get(plg, {}))
        if not verts_local:
            continue

        wx, wy, wz, wall_az = _origin_and_azimuth(w_attrs, spc_pts_local, True)
        tilt = _get_wall_tilt(w_attrs)

        pts = [Point3D(x, y, 0) for x, y in verts_local]
        if abs(tilt) > DOE2_ANGLE_TOL:
            ang = math.radians(tilt)
            axis = Vector3D(1, 0, 0)
            pts = [p.rotate(axis, ang, Point3D(0, 0, 0)) for p in pts]

        pts_space = _transform_points(pts, 180.0 - wall_az, (wx, wy, wz))
        pts_global = _transform_space_points(
            pts_space,
            Point3D(spc_pts_global[0].x, spc_pts_global[0].y, spc_pts_global[0].z),
            0,
            flr_origin,
            flr_az,
            glob_az
        )

        cmd = w_attrs.get('cmd')
        try:
            bc = _CMD_TO_BC[cmd]()
        except KeyError:
            raise ValueError('Unknown DOE2 surface command: {}'.format(cmd))

        t = abs(tilt % 360)
        if t > 180 - DOE2_ANGLE_TOL:
            t = 180 - t
        if 45 - DOE2_ANGLE_TOL <= t <= 135 + DOE2_ANGLE_TOL:
            ftype = Wall()
        else:
            if abs((tilt % 360) - 180) < DOE2_ANGLE_TOL:
                ftype = Floor()
            else:
                ftype = RoofCeiling()

        face = Face(
            identifier='{}_Face_{}'.format(clean_string(spc_name), idx),
            geometry=Face3D([Point3D(p.x, p.y, p.z) for p in pts_global]),
            type=ftype,
            boundary_condition=bc
        )
        # if an exterior wall check for doors and apertures
        if cmd == 'EXTERIOR-WALL' and len(pts_global) >= 2:
            gp1, gp2 = pts_global[0], pts_global[1]
            apps = _apertures_from_wall(cmd_dict, w_name, idx, gp1, gp2, base_z)
            drs = _doors_from_wall(cmd_dict, w_name, idx, gp1, gp2, base_z)
            if apps:
                face.add_apertures(apps)
            if drs:
                face.add_doors(drs)

        faces.append(face)
        idx += 1

    return faces


class _EdgeInfo:
    """Class for storing information about wall edges."""
    __slots__ = ('bc', 'apertures', 'doors')

    def __init__(self):
        self.bc = Outdoors()
        self.apertures = []
        self.doors = []


def _edge_info_map(cmd_dict, walls_dict, spc_verts_global, spc_verts_local):
    """Create a dict mapping each vertex index to its corresponding EdgeInfo object.

    Args:
        cmd_dict: Command dictionary containing all DOE2 objects.
        walls_dict: Dictionary of walls with their attributes, keyed by wall u_name.
        spc_verts_global: List of global space vertices that define the space footprint.
        spc_verts_local: List of local space vertices that define the space footprint.

    Returns:
        tuple[dict[int, _EdgeInfo], BoundaryCondition, BoundaryCondition]:
            - edge_info: map from vertex index to _EdgeInfo (with bc, apertures, doors)
            - floor_bc: The floor BoundaryCondition
            - ceiling_bc: The ceiling/roof BoundaryCondition

    """
    info = {i: _EdgeInfo() for i in range(len(spc_verts_global))}
    floor_bc = Outdoors()
    ceiling_bc = Outdoors()

    for w_name, w_attrs in walls_dict.items():
        tilt = _get_wall_tilt(w_attrs)

        if tilt == 90:
            _, idx = _wall_start_point(w_attrs, spc_verts_local)
            if idx < 0:
                continue
            cmd = w_attrs.get('cmd')
            try:
                info[idx].bc = _CMD_TO_BC[cmd]()
            except KeyError:
                raise ValueError('Unknown DOE2 surface command: {}'.format(cmd))

            p1 = spc_verts_global[idx]
            p2 = spc_verts_global[0] if idx == len(spc_verts_global) - 1 else \
                spc_verts_global[idx + 1]
            base_z = p1.z

            info[idx].apertures = \
                _apertures_from_wall(cmd_dict, w_name, idx, p1, p2, base_z)
            info[idx].doors = \
                _doors_from_wall(cmd_dict, w_name, idx, p1, p2, base_z)
        else:
            loc = w_attrs.get('LOCATION', '')
            cmd = w_attrs.get('cmd')
            if loc == 'TOP':
                ceiling_bc = _CMD_TO_BC[cmd]()
            elif loc == 'BOTTOM':
                floor_bc = _CMD_TO_BC[cmd]()
            else:
                pass

    return info, floor_bc, ceiling_bc


def _extruded_shell(spc_attrs, verts_glob, edge_info, floor_bc, ceiling_bc,
                    spc_name, flr_attrs):
    """Creates a list of honeybee Face objects representing the space shell geometry.

    Args:
        spc_attrs: Dictionary of space attributes.
        verts_glob: List of transformed vertices defining the space footprint.
        edge_info: Dictionary mapping vertex indices to corresponding EdgeInfo instances.
        floor_bc: The floor BoundaryCondition.
        ceiling_bc: The ceiling/roof BoundaryCondition.
        spc_name: Name of the current space.
        flr_attrs: Dictionary of floor attributes.

    Returns:
        list[Face]: A list of Face instances representing the complete space shell
    """
    faces = []
    vcount = len(verts_glob)
    height = _space_height(spc_attrs, flr_attrs)

    # Floor
    floor_pts = [Point3D(p.x, p.y, p.z) for p in verts_glob]
    faces.append(
        Face(
            identifier='{}_Floor'.format(clean_string(spc_name)),
            geometry=Face3D(floor_pts),
            type=Floor(),
            boundary_condition=floor_bc
        )
    )

    # Ceiling
    ceil_pts = [Point3D(p.x, p.y, p.z + height) for p in verts_glob]
    faces.append(
        Face(
            identifier='{}_Ceiling'.format(clean_string(spc_name)),
            geometry=Face3D(ceil_pts),
            type=RoofCeiling(),
            boundary_condition=ceiling_bc
        )
    )

    # Walls
    for i in range(vcount):
        p1 = verts_glob[i]
        p2 = verts_glob[0] if i == vcount - 1 else verts_glob[i + 1]
        wall_pts = [
            Point3D(p1.x, p1.y, p1.z),
            Point3D(p2.x, p2.y, p2.z),
            Point3D(p2.x, p2.y, p2.z + height),
            Point3D(p1.x, p1.y, p1.z + height),
        ]

        face = Face(
            identifier='{}_Wall_{}'.format(clean_string(spc_name), i + 1),
            geometry=Face3D(wall_pts),
            type=Wall(),
            boundary_condition=edge_info[i].bc
        )
        if edge_info[i].apertures:
            face.add_apertures(edge_info[i].apertures)
        if edge_info[i].doors:
            face.add_doors(edge_info[i].doors)
        faces.append(face)
    return faces


def _wall_start_point(wall_attrs, spc_verts_local):
    """Find the starting point and vertex index for a wall in global coordinates.

    Args:
        wall_attrs: Dictionary of wall attributes.
        spc_verts_local: List of local space vertices.

    Returns:
        tuple[float, float], int: A tuple containing:
            - The (x, y) coordinates of the wall's starting point
            - The index of the matching vertex in the spaces local coordinates
    """
    loc = wall_attrs.get('LOCATION', '')
    count = len(spc_verts_local)
    if loc.upper().startswith('SPACE-V'):
        n = int(loc.split('SPACE-V')[1])
        if 1 <= n <= count:
            v = spc_verts_local[n - 1]
            return (v.x, v.y), n - 1

    ox, oy, _ = _get_origin(wall_attrs)
    for i, v in enumerate(spc_verts_local):
        if abs(v.x - ox) < DOE2_TOLERANCE and abs(v.y - oy) < DOE2_TOLERANCE:
            return (v.x, v.y), i
    return None, -1


def _apertures_from_wall(cmd_dict, w_name, idx, gp1, gp2, z0):
    """Create aperture objects for windows in a wall.

    Args:
        cmd_dict: Command dictionary containing all DOE2 objects.
        w_name: Name of the parent wall.
        idx: Index of the wall's starting vertex.
        gp1: Point3D representing wall's start point.
        gp2: Point3D representing wall's end point.
        z0: Base height of the wall.

    Returns:
        list[Aperture]: List of Aperture objects for the wall
    """
    apps = []
    dx, dy = gp2.x - gp1.x, gp2.y - gp1.y
    length = math.hypot(dx, dy)
    if length < DOE2_TOLERANCE:
        return apps
    ux, uy = dx / length, dy / length

    wins = _child_objects_from_parent(cmd_dict, w_name, 'EXTERIOR-WALL', 'WINDOW')
    n = 1
    for win in wins.values():
        w = float(win.get('WIDTH', 0) or 0)
        h = float(win.get('HEIGHT', 0) or 0)
        xo = float(win.get('X', 0) or 0)
        yo = float(win.get('Y', 0) or 0)
        pts = _build_subface_corners((gp1.x, gp1.y), ux, uy, xo, yo, w, h, z0)
        apps.append(
            Aperture(
                '{}_Win{}_{}'.format(clean_string(w_name), idx, n),
                Face3D(pts),
                boundary_condition=Outdoors(),
            )
        )
        n += 1
    return apps


def _doors_from_wall(cmd_dict, w_name, idx, gp1, gp2, z0):
    """Create door objects for a wall.

    Args:
        cmd_dict: Command dictionary containing all DOE2 objects.
        w_name: Name of the parent wall.
        idx: Index of the wall's starting vertex.
        gp1: Point3D representing wall's start point.
        gp2: Point3D representing wall's end point.
        z0: Base height of the wall.

    Returns:
        list[Door]: List of Door objects for the wall.
    """
    doors = []
    dx, dy = gp2.x - gp1.x, gp2.y - gp1.y
    length = math.hypot(dx, dy)
    if length < DOE2_TOLERANCE:
        return doors
    ux, uy = dx / length, dy / length

    drs = _child_objects_from_parent(cmd_dict, w_name, 'EXTERIOR-WALL', 'DOOR')
    n = 1
    for d in drs.values():
        w = float(d.get('WIDTH', 3.0) or 3.0)
        h = float(d.get('HEIGHT', 7.0) or 7.0)
        xo = float(d.get("X", 0) or 0)
        yo = float(d.get("Y", 0) or 0)
        pts = _build_subface_corners((gp1.x, gp1.y), ux, uy, xo, yo, w, h, z0)
        doors.append(
            Door(
                '{}_Door{}_{}'.format(clean_string(w_name), idx, n),
                Face3D(pts),
                boundary_condition=Outdoors(),
            )
        )
        n += 1
    return doors


def _get_origin(attrs):
    """Return (x, y, z) coordinates from a DOE-2 object dict.

    Args:
        attrs: Dictionary containing DOE2 object attributes.

    Returns:
        tuple[float, float, float]: The (x, y, z) coordinates, defaulting to 0
        for any missing values.
    """
    return (
        float(attrs.get('X', 0) or 0),
        float(attrs.get('Y', 0) or 0),
        float(attrs.get('Z', 0) or 0),
    )


def _transform_points(pts, az_deg, origin_vec):
    """Rotate points about Z axis and then translate them.

    Args:
        pts (List[Point3D]): Points to transform.
        az_deg (float): Clock-wise rotation angle in degrees
        origin_vec (tuple[float, float, float]): Origin vector to translate the points

    Returns:
        list[Point3D]: The rotated + translated points
    """
    angle = math.radians(az_deg)
    dx, dy, dz = origin_vec
    move_vec = Vector3D(dx, dy, dz)
    out = []
    for p in pts:
        out.append(p.rotate_xy(angle, Point3D(0, 0, 0)).move(move_vec))
    return out


def _build_subface_corners(origin, ux, uy, offx, offy, width, height, z0):
    """Generate the four corner Point3D objects of a rectangular sub-surface.

    Args:
        origin (tuple[float, float, float]): Base point of the parent wall.
        ux (float): X-component of the wall
        uy (float): Y-component of the wall
        offx (float): Horizontal offset along the wall x-axis
        offy (float): Vertical offset above the wall base
        width (float): Horizontal extent of the rectangle.
        height (float): Vertical extent of the rectangle.
        z0 (float): Base elevation of the parent wall.

    Returns:
        list[Point3D]: Corner points as Point3D objects.
    """
    bl = Point3D(origin[0] + ux * offx, origin[1] + uy * offx, z0 + offy)
    br = Point3D(
        origin[0] + ux * (offx + width),
        origin[1] + uy * (offx + width),
        z0 + offy
    )
    tr = Point3D(br.x, br.y, z0 + offy + height)
    tl = Point3D(bl.x, bl.y, tr.z)
    return [bl, br, tr, tl]


def _verts_to_tuples(verts_dict):
    """Convert a DOE-2 POLYGON vertex string into a list of (x, y) float tuples.

    For example, a string like {'V1': '( 0, 0 )', 'V2': '( 10, 0 )', ...}
    will be converted into a list of tuples like [(0.0, 0.0), (10.0, 0.0), ...]

    Args:
        verts_dict: A dict of vertex labels and points.

    Returns:
        A list of (x, y) tuples as floats.
    """
    coord_pat = re.compile(r'\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)')
    pairs = coord_pat.findall(str(verts_dict))
    return [(float(x), float(y)) for x, y in pairs]


def _child_objects_from_parent(cmd_dict, parent_name, parent_command, child_command):
    """Return all child_command objects between a parent's line and its next sibling line.

    This requires the full dict of parsed INP blocks and one parent instance.

    Args:
        cmd_dict: Command dictionary containing all DOE2 objects.
        parent_name: Name of the parent from the object dict.
        parent_command: The command name of the parent.
        child_command: The command of the child objects to return.

    Returns:
        A dictionary with u_name strings for keys and dictionaries for values.
        This maps each child's u_name to its data dict whose __line__ is between
        the two parent lines.
    """
    # Sort the parents by __line__ just in case
    parents = cmd_dict.get(parent_command, {})
    sorted_parents = sorted(
        parents.items(),
        key=lambda item: item[1].get('__line__', float('inf'))
    )

    # Get the start line and end line
    start_line = None
    end_line = float('inf')
    for idx, (u_name, attrs) in enumerate(sorted_parents):
        if u_name == parent_name:
            start_line = attrs.get("__line__", -1)
            # find the next parents line , this will be the stopping point
            if idx + 1 < len(sorted_parents):
                end_line = sorted_parents[idx + 1][1].get('__line__', float('inf'))
            break

    # If we cant find the start then return empty dict
    if start_line is None:
        return {}

    # Find children in between the line
    children = cmd_dict.get(child_command, {})
    in_block = {
        c_name: c_data
        for c_name, c_data in children.items()
        if start_line < c_data.get('__line__', -1) < end_line
    }

    return in_block


def _surfaces_from_space(cmd_dict, space_name):
    """Return all surface‐type child objects (e.g., walls, roofs) for a given SPACE.

    Args:
        cmd_dict: Command dictionary containing all DOE2 objects.
        space_name (str):  Unique name of the SPACE object.

    Returns:
        A dictionary mapping each surface U-name to its attributes for all
        surfaces under this space.
    """
    surf_types = ['EXTERIOR-WALL', 'INTERIOR-WALL', 'UNDERGROUND-WALL', 'ROOF']
    surfs = {}
    for surf in surf_types:
        children = _child_objects_from_parent(cmd_dict, space_name, 'SPACE', surf)
        surfs.update(children)
    return surfs


def _calc_azimuth(v1, v2):
    """Calculate the azimuth from point v1 to v2 in degrees clockwise from north.

    Args:
        v1 (tuple[float, float]): (x, y) coordinates of the first point.
        v2 (tuple[float, float]): (x, y) coordinates of the second point.

    Returns:
        float: Azimuth angle in degrees in the range [0, 360].
    """
    dx, dy = v2[0] - v1[0], v2[1] - v1[1]
    ang = math.degrees(math.atan2(dy, dx))
    return ang + 360 if ang < 0 else ang


def _get_wall_tilt(w_attrs):
    """Return the wall’s tilt angle in degrees, with overrides for special LOCATIONs.

    Args:
        w_attrs (dict): Attributes dictionary for the wall object.

    Returns:
        float: Tilt angle (0 = horizontal up, 90 = vertical, 180 = horizontal down).
    """
    loc = (w_attrs.get('LOCATION') or '').upper()
    try:
        tilt = float(w_attrs.get("TILT", 90) or 90)
    except (TypeError, ValueError):
        tilt = 90
    if loc.startswith('SPACE-V'):
        return 90
    if loc == 'TOP':
        return 0
    if loc == 'BOTTOM':
        return 180
    return tilt


def _origin_and_azimuth(obj_attrs, parent_vertices, is_wall):
    """Compute the local origin (x, y, z) and azimuth for a SPACE, WALL, or FLOOR.

    Args:
        obj_attrs (dict): Attributes dictionary for the object (SPACE or WALL).
        parent_vertices (list[tuple[float, float]]): Vertex list of the parent polygon
            or None for FLOOR.

    Returns:
        tuple: (x, y, z, azimuth)
            x, y, z : float origin coordinates.
            azimuth (float): Azimuth in degrees .
    """
    loc = (obj_attrs.get('LOCATION') or '').upper()
    if loc.startswith(('SPACE-V', 'FLOOR-V')):
        idx = int(loc.split('-V', 1)[1]) - 1
        v1 = parent_vertices[idx]
        nxt = 0 if idx + 1 == len(parent_vertices) else idx + 1
        v2 = parent_vertices[nxt]
        x, y = v1
        z = float(obj_attrs.get("Z", 0) or 0)
        az = _calc_azimuth(v1, v2)
    else:
        x, y, z = _get_origin(obj_attrs)
        az = float(obj_attrs.get('AZIMUTH', 0) or 0)
        if not is_wall:
            az = - az  # Reverse azimuth for SPACE and FLOOR
    return x, y, z, az


def _space_height(spc_attrs, flr_attrs):
    """Return the height of a SPACE in feet.

    Args:
        spc_attrs (dict): Attributes dictionary for the SPACE.
        flr_attrs (dict): Attributes dictionary for the parent FLOOR.

    Returns:
        float: Height of the space (ft).

    Raises:
        ValueError: If neither SPACE["HEIGHT"], FLOOR["SPACE-HEIGHT"], nor
                    FLOOR["FLOOR-HEIGHT"] is provided.
    """
    def _to_float(val):
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    h = _to_float(spc_attrs.get('HEIGHT'))
    if h is not None:
        return h
    h = _to_float(flr_attrs.get('SPACE-HEIGHT'))
    if h is not None:
        return h
    h = _to_float(flr_attrs.get('FLOOR-HEIGHT'))
    if h is not None:
        return h

    err_msg = 'Cannot determine height for Space: ' \
        'missing "HEIGHT", "SPACE-HEIGHT", or "FLOOR-HEIGHT".'
    raise ValueError(err_msg)


def _transform_space_points(local_pts, space_origin, spc_az,
                            floor_origin, flr_az, glob_az):
    """Convert space‐local vertices to global coordinates (feet).

    Args:
        local_pts (list[Point3D]): Vertices in space-local coords (feet).
        space_origin (Point3D): Origin of the space in parent coords.
        spc_az (float): Space azimuth in degrees.
        floor_origin (Point3D): Origin of the floor in global coords.
        flr_az (float): Floor azimuth in degrees.
        glob_az (float): Building azimuth in degrees.

    Returns:
        list[Point3D]: Transformed vertices in global coords (feet).
    """
    if not local_pts:
        return []

    # Rotate by space azimuth
    if abs(spc_az) > DOE2_TOLERANCE:
        ang = math.radians(spc_az)
        local_pts = [p.rotate_xy(ang, Point3D(0, 0, 0)) for p in local_pts]

    # Translate to space origin
    space_vec = Vector3D(space_origin.x, space_origin.y, space_origin.z)
    pts = [p.move(space_vec) for p in local_pts]

    # Rotate by floor azimuth
    if abs(flr_az) > DOE2_TOLERANCE:
        ang = math.radians(flr_az)
        pts = [p.rotate_xy(ang, Point3D(0, 0, 0)) for p in pts]

    # Rotate by building azimuth
    if abs(glob_az) > DOE2_TOLERANCE:
        ang = math.radians(glob_az)
        pts = [p.rotate_xy(ang, Point3D(0, 0, 0)) for p in pts]

    # Translate to floor origin
    floor_vec = Vector3D(floor_origin.x, floor_origin.y, floor_origin.z)
    return [p.move(floor_vec) for p in pts]
