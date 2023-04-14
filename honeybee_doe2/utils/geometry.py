from ladybug_geometry.geometry3d import Point3D, Face3D
from ladybug_geometry.geometry2d import Polygon2D, Point2D

from honeybee.facetype import Floor


def get_floor_boundary(rooms):
    """Get a list of vertices for floor boundary for a list of rooms.

    This function joins all the floor faces and returns a list of Point3D that define the
    border of the floor in counter clockwise order starting from the lower left corner.

    If the flip is set to True the floor faces will be flipped.
    """
    floor_geom = []

    for room in rooms:
        for face in room.faces:
            if isinstance(face.type, Floor):
                floor_geom.append(face.geometry)

    # get the minimum z and use it for all the floors
    z = min(geo.plane.o.z for geo in floor_geom)
    boundaries = []
    # floors are most likely horizontal - let's make them 2D polygons
    for floor in floor_geom:
        boundary = Polygon2D(
            [
                Point2D(v.x, v.y) for v in floor.lower_left_counter_clockwise_vertices
            ]
        )
        boundaries.append(boundary)

    # find the union of the boundary polygons
    boundaries = Polygon2D.boolean_union_all(boundaries, tolerance=0.01)

    # I don't know if this is the right assumption
    assert len(boundaries) == 1, \
        'Input story generates more than one polygon ' \
        f'[{len(boundaries)}]. Not in DOE2!'

    boundary = [
        Point3D(point.x, point.y, z) for point in boundaries[0].vertices
    ]

    vertices = Face3D(
        boundary,
        plane=floor_geom[0].plane
    ).lower_left_counter_clockwise_vertices

    return vertices
