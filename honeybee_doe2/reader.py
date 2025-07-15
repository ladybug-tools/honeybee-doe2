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
from honeybee.door import Door as HbDoor
from honeybee_energy.boundarycondition import Adiabatic
from honeybee.boundarycondition import Outdoors, Ground
from honeybee.typing import clean_string

from .config import DOE2_ANGLE_TOL, GEO_DEC_COUNT
from .util import clean_inp_file_contents, doe2_object_blocks, parse_inp_string


_FEET_TO_METERS = 0.3048
_TOL            = 1e-6         # 1 mm 

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
    non_parameter_blocks = []
    block_line_count = 1

    # Get globals first since they are formatted slightly differently
    for blk in blocks:
        u_name, cmd, keys, vals = parse_inp_string(blk)
        if cmd == "PARAMETER":
            key, val_raw = keys[0], vals[0]
            try:
                global_parameters[key] = float(val_raw)
            except ValueError:
                global_parameters[key] = val_raw
        else:
            non_parameter_blocks.append(blk)

    result = defaultdict(dict)

    for blk in non_parameter_blocks:
        u_name, cmd, keys, vals = parse_inp_string(blk)

        if keys is None or vals is None:
            continue  # ignore the block if it does not have any keywords

        attr_d = {}
        for k, v in zip(keys, vals):
            try:
                attr_d[k] = float(v)
            except ValueError:
                attr_d[k] = v
        attr_d["__line__"] = block_line_count
        attr_d["cmd"] = cmd 
        block_line_count += 1
        result[cmd][u_name] = attr_d

    if global_parameters:
        result["PARAMETER"] = global_parameters

    return dict(result)

def model_from_inp(inp_file_path):
    """Convert an inp file to an HBJSON Model object

    Args:
        inp_file_path: The file path to an inp file

    Returns:
        A honeybee Model object. This only converts the geometry 

    """
    with open(inp_file_path, 'r') as doe_file:
        inp_file_contents = doe_file.read()

    inp = command_dict_from_inp(inp_file_contents)
    floors = inp.get("FLOOR", {})
    polys  = inp.get("POLYGON", {})
    glob_az = float(inp.get("BUILD-PARAMETERS", {}).get("AZIMUTH", 0) or 0)

    if not floors:
        raise ValueError("No FLOOR objects found in INP – nothing to translate.")

    rooms = []

    for flr_name, flr in floors.items():
        fx, fy, fz = _get_origin(flr)
        flr_origin = Point3D(fx, fy, fz)
        flr_az     = float(flr.get("AZIMUTH", 0) or 0)
        floor_poly = (flr.get("POLYGON") or "").strip('"')
        floor_verts = _verts_to_tuples(polys.get(floor_poly, {}))

        spaces = child_objects_from_parent(inp, flr_name, "FLOOR", "SPACE")
        for spc_name, spc in spaces.items():
            shape = (spc.get("SHAPE") or "").upper()
            if not shape or shape == "NO-SHAPE":
                continue
            if shape == "BOX":
                raise ValueError(f"{spc_name} is defined by a BOX – convert to POLYGON first.")

            # local footprint
            plg = spc.get("POLYGON", "").strip('"')
            verts_local = _verts_to_tuples(polys.get(plg, {}))
            if not verts_local:
                continue
            pts_local = [Point3D(x, y, 0) for x, y in verts_local]

            # space transform
            sx, sy, sz, spc_az = _space_origin_and_azimuth(spc, floor_verts)
            spc_points = _transform_space_points(
                pts_local,
                Point3D(sx, sy, sz),
                spc_az,
                flr_origin,
                flr_az,
                glob_az
            )

            walls = surfaces_from_space(inp, spc_name)
            detailed = walls and all(w.get("POLYGON") for w in walls.values()) # If all walls are POLYGON shape
            if detailed:
                faces = _volume_from_polygons(walls, 
                    polys,
                    spc_points, pts_local, spc_name, 
                    flr_origin, flr_az, glob_az,  
                    inp
                )
            else:
                edge_info = _edge_info_map(walls, spc_points, inp)
                faces = _extruded_shell(spc, spc_points, edge_info, spc_name, flr)

            room = Room(identifier=clean_string(spc_name), faces=faces)
            room.display_name = spc_name
            room.story = flr_name
            rooms.append(room)

    model_name = clean_string(os.path.splitext(os.path.basename(inp_file_path))[0])
    return Model(model_name, rooms)


def _volume_from_polygons(walls, polys, spc_pts_global, spc_pts_local, spc_name, flr_origin, flr_az, glob_az, inp_dict):
    """Build detailed faces when each wall has its own POLYGON."""
    faces = []
    idx = 1

    base_z = spc_pts_global[0].z if spc_pts_global else 0

    for w_name, w_attrs in walls:
        plg = (w_attrs.get("POLYGON") or "").strip('"')
        verts_local = _verts_to_tuples(polys.get(plg, {}))
        if not verts_local:
            continue

        wx, wy, wz = _get_origin(w_attrs)
        wall_az    = float(w_attrs.get("AZIMUTH", 0) or 0)
        loc        = w_attrs.get("LOCATION","") 

        if loc.startswith("SPACE-V"):
            try:
                edge = int(loc[7:]) - 1
                if 0 <= edge < len(spc_pts_local):
                    wx, wy = spc_pts_local[edge]
                    next_i = 0 if edge + 1 == len(spc_pts_local) else edge + 1 # check if its the last vert
                    wall_az = _calc_azimuth(spc_pts_local[edge], spc_pts_local[next_i])
            except:
                pass

        try:
            tilt = float(w_attrs.get("TILT", 90) or 90)
        except:
            tilt = 90
        if loc.startswith("SPACE-V"): 
            tilt = 90
        elif loc == "TOP":
            tilt = 0
        elif loc == "BOTTOM":
            tilt = 180

        pts = [Point3D(x, y, 0) for x, y in verts_local]
        if abs(tilt) > 1e-9:
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

        cmd = w_attrs.get("cmd")
        if cmd.startswith("INTERIOR"):
            bc = Adiabatic()
        elif cmd.startswith("UNDER"):
            bc = Ground()
        else:
            bc = Outdoors()

        t = abs(tilt % 360)
        if t > 180 - DOE2_ANGLE_TOL:
            t = 180 - t
        if 45 - DOE2_ANGLE_TOL <= t <= 135 + DOE2_ANGLE_TOL:
            ftype = Wall()
        else:
            if loc == "BOTTOM" or abs((tilt % 360) - 180) < DOE2_ANGLE_TOL:
                ftype = Floor()
            else:
                ftype = RoofCeiling()

        face = Face(
            identifier=f"{clean_string(spc_name)}_Face_{idx}",
            geometry=Face3D([_feet_to_meters((p.x, p.y, p.z)) for p in pts_global]),
            type=ftype,
            boundary_condition=bc
        )
        #If an exterior wall check for doors and aperatures
        if cmd.startswith("EXTERIOR") and len(pts_global) >= 2:
            gp1, gp2 = pts_global[0], pts_global[1]
            apps = _apertures_from_wall(inp_dict, w_name, idx, gp1, gp2, base_z)
            drs  = _doors_from_wall(inp_dict, w_name, idx, gp1, gp2, base_z)
            if apps:
                face.add_apertures(apps)
            if drs:
                face.add_doors(drs)

        faces.append(face)
        idx += 1

    return faces


class _EdgeInfo:
    __slots__ = ("bc", "apertures", "doors")
    def __init__(self):
        self.bc    = "outdoors" # convert the string backto a boundry condition 
        self.apertures  = []
        self.doors = []


def _edge_info_map(walls_dict, verts_glob, objectdict):  
    """Creates a dictionary mapping each vertex index to its corresponding EdgeInfo object

    Parameters:
        walls_attr: Dict of walls with their attributes, keyed by wall u_name.
        verts_glob: List of transformed space verts that define the space footprint
        objectdict: The command dict repersenting all the DOE2 objects in the inp file

    Returns:
            A dictionary mapping vertex indexs to _EdgeInfo instances, populated with:
                - Boundary conditions ('adiabatic', 'ground', 'outdoors').
                - Lists of apertures and doors positioned along each edge.
    """
    info = {i: _EdgeInfo() for i in range(len(verts_glob))}

    for w_name, wall_attrs in walls_dict.items():
        start, idx = _wall_start_point(wall_attrs, verts_glob)
        if idx < 0:
            continue

        wtyp = (wall_attrs.get("cmd") or "").upper()
        
        if wtyp.startswith("INTERIOR"):
            info[idx].bc = "adibatic"
        elif wtyp.startswith("UNDER"):
            info[idx].bc = "ground"
        else:
            info[idx].bc = "outdoors"

        if not wtyp.startswith("EXTERIOR"):
            continue

        p1 = verts_glob[idx]
        p2 = verts_glob[0] if idx == len(verts_glob) - 1 else verts_glob[idx + 1]
        base_z = p1.z

        info[idx].apertures = _apertures_from_wall(objectdict, w_name, idx, p1, p2, base_z)
        info[idx].doors     = _doors_from_wall(objectdict, w_name, idx, p1, p2, base_z)

    return info


def _extruded_shell(spc_attrs, verts_glob, edge_info, spc_name, flr_attrs):
    """Creates a list of honeybee Face objects representing the space shell geometry (floor, ceiling, walls).

    Parameters:
        spc_attrs: Dict of space attributes 
        verts_glob: List of transformed vertices defining the space footprint
        edge_info: Dictionary mapping vertex indices to corresponding EdgeInfo instances.
        spc_name: Name current space.
        flr_attrs: Dict of floor attributes

    Returns:
        A list of Face instances, each representing:
            - Floor face (boundary condition: ground).
            - Ceiling face (boundary condition: outdoors).
            - Wall faces, each populated with:
                - Appropriate boundary condition ('adiabatic', 'ground', 'outdoors').
                - Apertures and doors, if present.
    """
    faces = []
    vcount = len(verts_glob)
    height = _space_height(spc_attrs, flr_attrs)

    # floor
    floor_m = [_feet_to_meters((p.x, p.y, p.z)) for p in verts_glob]
    faces.append(
        Face(
            identifier= f"{clean_string(spc_name)}_Floor",
            geometry= Face3D(floor_m),
            type=Floor(),  
            boundary_condition=Ground()
        )
    )

    # ceiling
    ceil_m = [_feet_to_meters((p.x, p.y, p.z + height)) for p in verts_glob]
    faces.append(
        Face(
            identifier= f"{clean_string(spc_name)}_Ceiling",
            geometry= Face3D(ceil_m),
            type=RoofCeiling(), 
            boundary_condition=Outdoors()
        )
    )

    # walls
    for i in range(vcount):
        p1 = verts_glob[i]
        p2 = verts_glob[0] if i == vcount - 1 else verts_glob[i + 1]
        wall_ft = [
            (p1.x, p1.y, p1.z),
            (p2.x, p2.y, p2.z),
            (p2.x, p2.y, p2.z + height),
            (p1.x, p1.y, p1.z + height),
        ]
        wall_m = [_feet_to_meters(pt) for pt in wall_ft]

        bc_string = edge_info[i].bc
        if bc_string == "adiabatic":
            bc = Adiabatic()
        elif bc_string == "ground":
            bc = Ground()
        else:
            bc = Outdoors()

        face = Face(
            identifier=f"{clean_string(spc_name)}_Wall_{i + 1}",
            geometry=Face3D(wall_m),
            type=Wall(), 
            boundary_condition = Outdoors()
        )
        if edge_info[i].apertures:
            face.add_apertures(edge_info[i].apertures) 
        if edge_info[i].doors:
            face.add_doors(edge_info[i].doors) 
        faces.append(face)
    return faces


# Wall Helpers
def _wall_start_point(wall_attrs, verts_glob):
    loc = wall_attrs.get("LOCATION", "")
    count = len(verts_glob)
    if loc.upper().startswith("SPACE-V"):
        n = int(loc.split("SPACE-V")[1])
        if 1 <= n <= count:
            v = verts_glob[n - 1]
            return (v.x, v.y), n - 1

    ox, oy, _ = _get_origin(wall_attrs)
    for i, v in enumerate(verts_glob):
        if abs(v.x - ox) < _TOL and abs(v.y - oy) < _TOL:
            return (v.x, v.y), i
    return None, -1


def _apertures_from_wall(objectdict, w_name, idx, gp1, gp2, z0):
    apps = []
    dx, dy = gp2.x - gp1.x, gp2.y - gp1.y
    length = math.hypot(dx, dy)
    if length < _TOL:
        return apps
    ux, uy = dx / length, dy / length

    wins = child_objects_from_parent(objectdict, w_name, "EXTERIOR-WALL", "WINDOW")
    n = 1
    for win in wins.values():
        w  = float(win.get("WIDTH", 0) or 0)
        h  = float(win.get("HEIGHT", 0) or 0)
        xo = float(win.get("X", 0) or 0)
        yo = float(win.get("Y", 0) or 0)
        pts_ft = _build_subface_corners((gp1.x, gp1.y), ux, uy, xo, yo, w, h, z0)
        apps.append(
            Aperture(
                f"{clean_string(w_name)}_Win{idx}_{n}",
                Face3D([_feet_to_meters(p) for p in pts_ft]),
                boundary_condition=Outdoors(),
            )
        )
        n += 1
    return apps


def _doors_from_wall(objectdict, w_name, idx, gp1, gp2, z0):
    doors = []
    dx, dy = gp2.x - gp1.x, gp2.y - gp1.y
    length = math.hypot(dx, dy)
    if length < _TOL:
        return doors
    ux, uy = dx / length, dy / length

    drs = child_objects_from_parent(objectdict, w_name, "EXTERIOR-WALL", "DOOR")
    n = 1
    for d in drs.values():
        w  = float(d.get("WIDTH", 3.0) or 3.0)
        h  = float(d.get("HEIGHT", 7.0) or 7.0)
        xo = float(d.get("X", 0) or 0)
        yo = float(d.get("Y", 0) or 0)
        pts_ft = _build_subface_corners((gp1.x, gp1.y), ux, uy, xo, yo, w, h, z0)
        doors.append(
            HbDoor(
                f"{clean_string(w_name)}_Door{idx}_{n}",
                Face3D([_feet_to_meters(p) for p in pts_ft]),
                boundary_condition= Outdoors(),
            )
        )
        n += 1
    return doors


# Helpers
def _get_origin(attrs):
    """Return (x, y, z) from a DOE-2 object dict, default 0."""
    return (
        float(attrs.get("X", 0) or 0),
        float(attrs.get("Y", 0) or 0),
        float(attrs.get("Z", 0) or 0),
    )


def _feet_to_meters(pt):
    """(x, y, z) in ft → Point3D in m."""
    return Point3D(pt[0] * _FEET_TO_METERS,
                   pt[1] * _FEET_TO_METERS,
                   pt[2] * _FEET_TO_METERS)


def _transform_points(pts, az_deg, origin_vec):
    """
    Rotate a list of Point3D about Z, then translate by (dx,dy,dz).
    """
    angle = math.radians(az_deg)
    dx, dy, dz = origin_vec
    move_vec = Vector3D(dx, dy, dz)
    out = []
    for p in pts:
        out.append(p.rotate_xy(angle, Point3D(0, 0, 0)).move(move_vec))
    return out


def _build_subface_corners(origin, ux, uy, offx, offy, width, height, z0):
    """"""
    bl = [origin[0] + ux * offx, origin[1] + uy * offx, z0 + offy]
    br = [origin[0] + ux * (offx + width), origin[1] + uy * (offx + width), z0 + offy]
    tr = [br[0], br[1], z0 + offy + height]
    tl = [bl[0], bl[1], tr[2]]
    return [bl, br, tr, tl]


def _verts_to_tuples(text):
    """
    Converts a DOE-2 POLYGON  verts string like:
        {'V1': '( 0, 0 )', 'V2': '( 10, 0 )', ...}
    into a list of (x, y) float tuples like:
        [(0.0, 0.0), (10.0, 0.0), ...]

    Args:
        text: A string representation of a DOE-2 polygon vertex dictionary.

    Returns:
        A list of (x, y) tuples as floats
    """
    _coord_pat = re.compile(r'\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)')
    pairs = _coord_pat.findall(str(text))    
    return [(float(x), float(y)) for x, y in pairs]

def child_objects_from_parent(objectdict, parent_name, parent_command, child_command):
    """
    Given the full dict of parsed INP blocks, and one parent instance,
    return all of the child_command objects that fall between that
    parent’s line and its next‐sibling parent’s line.

    Args:
        objectdict: A dictionary of parsed INP blocks
        parent_name: Name of the parent from the objectdict
        parent_command: The command name of the parent
        child_command: The command of the child objects to return

    Returns:
        Dict[str, dict]:  A mapping of each child’s u_name → its data dict
                         whose __line__ is between the two parent lines.
    """

    # Sort the parents by __line__ just in case
    parents = objectdict.get(parent_command, {})
    sorted_parents = sorted(
        parents.items(),
        key=lambda item: item[1].get("__line__", float("inf"))
    )

    # Get the start line and end line
    start_line = None
    end_line = float("inf")
    for idx, (u_name, attrs) in enumerate(sorted_parents):
        if u_name == parent_name:
            start_line = attrs.get("__line__", -1)
            # find the next parent's line , this will be the stopping point
            if idx + 1 < len(sorted_parents):
                end_line = sorted_parents[idx + 1][1].get("__line__", float("inf"))
            break

    # If we cant find the start then return empty dict
    if start_line is None:
        return {}

    # find children in between the line
    children = objectdict.get(child_command, {})
    in_block = {
        c_name: c_data
        for c_name, c_data in children.items()
        if start_line < c_data.get("__line__", -1) < end_line
    }

    return in_block

def surfaces_from_space(objectdict, space_name):
    """
    Return all surface-type child objects (e.g., walls, roofs) for a given SPACE.

    Args:
        objectdict: The full parsed INP dictionary.
        space_name: Unique name of the SPACE object.

    Returns:
        Dict[str, dict]: A dictionary of all surface objects under this space
    """
    surf_types = ['EXTERIOR-WALL', 'INTERIOR-WALL', 'UNDERGROUND-WALL', 'ROOF']
    surfs = {}
    for surf in surf_types:
        children = child_objects_from_parent(objectdict, space_name, "SPACE", surf)
        surfs.update(children)
    return surfs

def _calc_azimuth(v1, v2):
    """
    """
    dx, dy = v2[0] - v1[0], v2[1] - v1[1]
    ang = math.degrees(math.atan2(dy, dx))  
    return ang + 360 if ang < 0 else ang   

def _space_origin_and_azimuth(spc_attrs, floor_vertices):
    """
    """
    loc = (spc_attrs.get("LOCATION") or "").upper()

    if loc.startswith("FLOOR-V"):
        idx = int(loc[7:])            
        v1 = floor_vertices[idx - 1]
        v2 = floor_vertices[0 if idx == len(floor_vertices) else idx]
        sx, sy = v1
        sz = float(spc_attrs.get("Z", 0) or 0)
        spc_az_cw = _calc_azimuth(v1, v2)       
    else:
        sx,sy,sz = _get_origin(spc_attrs)
        spc_az_cw = -float(spc_attrs.get("AZIMUTH", 0) or 0)
    return sx, sy, sz, spc_az_cw


def _space_height(spc_attrs, flr_attrs):
    """
    Return the height of a SPACE. 

    Ar

    """
    def _to_float(val):
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    h = _to_float(spc_attrs.get("HEIGHT"))
    if h is not None:
        return h

    h = _to_float(flr_attrs.get("SPACE-HEIGHT"))
    if h is not None:
        return h

    h = _to_float(flr_attrs.get("FLOOR-HEIGHT"))
    if h is not None:
        return h

    raise ValueError(
        "Cannot determine height for Space, missing HEIGHT attribute or parent floor is missing"
        "is missing 'SPACE-HEIGHT' or 'FLOOR-HEIGHT attribute"
    )






def _transform_space_points(local_pts, space_origin, spc_az, floor_origin, flr_az, glob_az):
    """

    """
    if not local_pts:
        return []

    # Rotate around its own origin first
    if abs(spc_az) > 1e-9:
        ang = math.radians(spc_az)
        local_pts = [p.rotate_xy(ang, Point3D(0, 0, 0)) for p in local_pts]

    # Translate the points
    space_vec = Vector3D(space_origin.x, space_origin.y, space_origin.z)
    pts = [p.move(space_vec) for p in local_pts]

    # Rotate about the floor azimuth
    if abs(flr_az) > 1e-9:
        pts = [p.rotate_xy(math.radians(-flr_az), Point3D(0, 0, 0)) for p in pts]

    # Rotate about the building azimuth if there is one
    if abs(glob_az) > 1e-9:
        pts = [p.rotate_xy(math.radians(-glob_az), Point3D(0, 0, 0)) for p in pts]

    # Move the points 
    floor_vec = Vector3D(floor_origin.x, floor_origin.y, floor_origin.z)
    return [p.move(floor_vec) for p in pts]




     


