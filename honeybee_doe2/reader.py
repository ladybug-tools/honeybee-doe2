import os
from math import radians, sin, cos
from typing import Tuple, List
from ladybug_geometry.geometry3d import Point3D, Face3D
from ladybug_geometry.geometry2d import Point2D
from ladybug_geometry.geometry3d import Plane, Vector3D
from .util import parse_inp_file      
from .config import DOE2_ANGLE_TOL, GEO_DEC_COUNT

def model_from_inp(inp_file_path):
    """
    Read a DOE-2 INP file and return a Honeybee model.
    
    Args:
        inp_file_path: A path to the INP file to read.

    Returns:
        A Honeybee model.   

        TODO: Loop over the inp_object_dict and create the Honeybee model.
    """
    inp_object_dict = parse_inp_file(inp_file_path)

 


