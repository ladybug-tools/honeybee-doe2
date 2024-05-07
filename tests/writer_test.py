"""Test the translators for geometry to INP."""
from ladybug_geometry.geometry3d import Point3D, Vector3D, Mesh3D

from honeybee.model import Model
from honeybee.room import Room
from honeybee.face import Face
from honeybee.aperture import Aperture
from honeybee.door import Door
from honeybee.shade import Shade
from honeybee.shademesh import ShadeMesh

from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.material.opaque import EnergyMaterial
from honeybee_energy.schedule.ruleset import ScheduleRuleset
import honeybee_energy.lib.scheduletypelimits as schedule_types
from honeybee_energy.lib.programtypes import office_program, program_type_by_identifier


def test_shade_writer():
    """Test the basic functionality of the Shade inp writer."""
    rect_verts = [[0, 0, 3], [1, 0, 3], [1, 1, 3], [0, 1, 3]]
    non_rect_verts = [[0, 0, 3], [1, 0, 3], [2, 1, 3], [0, 1, 3]]
    shade = Shade.from_vertices('overhang', rect_verts)

    shade_polygon, shade_def = shade.to.inp(shade)
    assert shade_polygon == ''
    assert shade_def == \
       '"overhang" = FIXED-SHADE\n' \
       '   SHAPE                    = RECTANGLE\n' \
       '   HEIGHT                   = 1.0\n' \
       '   WIDTH                    = 1.0\n' \
       '   X-REF                    = 0.0\n' \
       '   Y-REF                    = 0.0\n' \
       '   Z-REF                    = 3.0\n' \
       '   TILT                     = 0.0\n' \
       '   AZIMUTH                  = 180.0\n' \
       '   TRANSMITTANCE            = 0\n' \
       '   ..\n'

    shade = Shade.from_vertices('overhang', non_rect_verts)
    shade_polygon, shade_def = shade.to.inp(shade)
    assert shade_polygon == \
       '"overhang Plg" = POLYGON\n' \
       '   V1                       = (0.0, 0.0)\n' \
       '   V2                       = (1.0, 0.0)\n' \
       '   V3                       = (2.0, 1.0)\n' \
       '   V4                       = (0.0, 1.0)\n' \
       '   ..\n'
    assert shade_def == \
       '"overhang" = FIXED-SHADE\n' \
       '   SHAPE                    = POLYGON\n' \
       '   POLYGON                  = "overhang Plg"\n' \
       '   X-REF                    = 0.0\n' \
       '   Y-REF                    = 0.0\n' \
       '   Z-REF                    = 3.0\n' \
       '   TILT                     = 0.0\n' \
       '   AZIMUTH                  = 180.0\n' \
       '   TRANSMITTANCE            = 0\n' \
       '   ..\n'

    fritted_glass_trans = ScheduleRuleset.from_constant_value(
        'Fritted Glass', 0.5, schedule_types.fractional)
    shade.properties.energy.transmittance_schedule = fritted_glass_trans
    shade_polygon, shade_def = shade.to.inp(shade)
    assert shade_def == \
       '"overhang" = FIXED-SHADE\n' \
       '   SHAPE                    = POLYGON\n' \
       '   POLYGON                  = "overhang Plg"\n' \
       '   X-REF                    = 0.0\n' \
       '   Y-REF                    = 0.0\n' \
       '   Z-REF                    = 3.0\n' \
       '   TILT                     = 0.0\n' \
       '   AZIMUTH                  = 180.0\n' \
       '   TRANSMITTANCE            = 0.5\n' \
       '   ..\n'

    move_vals = [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1,
                 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0]
    moveable_trans = ScheduleRuleset.from_daily_values('Moveable Awning', move_vals)
    shade.properties.energy.transmittance_schedule = moveable_trans
    shade_polygon, shade_def = shade.to.inp(shade)
    assert shade_def == \
       '"overhang" = FIXED-SHADE\n' \
       '   SHAPE                    = POLYGON\n' \
       '   POLYGON                  = "overhang Plg"\n' \
       '   X-REF                    = 0.0\n' \
       '   Y-REF                    = 0.0\n' \
       '   Z-REF                    = 3.0\n' \
       '   TILT                     = 0.0\n' \
       '   AZIMUTH                  = 180.0\n' \
       '   TRANSMITTANCE            = 0.417\n' \
       '   SHADE-SCHEDULE           = "Moveable Awning"\n' \
       '   ..\n'


def test_shade_mesh_writer():
    """Test the basic functionality of the ShadeMesh inp writer."""
    pts = (Point3D(0, 0, 4), Point3D(0, 2, 4), Point3D(2, 2, 4),
           Point3D(2, 0, 4), Point3D(4, 0, 4))
    mesh = Mesh3D(pts, [(0, 1, 2, 3), (2, 3, 4)])
    shade = ShadeMesh('Awning_1', mesh)

    shade_polygons, shade_defs = shade.to.inp(shade)
    assert len(shade_polygons) == 1
    assert len(shade_defs) == 2
    assert shade_polygons[0] == \
       '"Awning 11 Plg" = POLYGON\n' \
       '   V1                       = (0.0, 0.0)\n' \
       '   V2                       = (2.0, 0.0)\n' \
       '   V3                       = (0.0, 2.0)\n' \
       '   ..\n'
    assert shade_defs[0] == \
       '"Awning 10" = FIXED-SHADE\n' \
       '   SHAPE                    = RECTANGLE\n' \
       '   HEIGHT                   = 2.0\n' \
       '   WIDTH                    = 2.0\n' \
       '   X-REF                    = 0.0\n' \
       '   Y-REF                    = 0.0\n' \
       '   Z-REF                    = 4.0\n' \
       '   TILT                     = 0.0\n' \
       '   AZIMUTH                  = 180.0\n' \
       '   TRANSMITTANCE            = 0\n' \
       '   ..\n'
    assert shade_defs[1] == \
       '"Awning 11" = FIXED-SHADE\n' \
       '   SHAPE                    = POLYGON\n' \
       '   POLYGON                  = "Awning 11 Plg"\n' \
       '   X-REF                    = 2.0\n' \
       '   Y-REF                    = 0.0\n' \
       '   Z-REF                    = 4.0\n' \
       '   TILT                     = 0.0\n' \
       '   AZIMUTH                  = 180.0\n' \
       '   TRANSMITTANCE            = 0\n' \
       '   ..\n'
   
    fritted_glass_trans = ScheduleRuleset.from_constant_value(
         'Fritted Glass', 0.5, schedule_types.fractional)
    shade.properties.energy.transmittance_schedule = fritted_glass_trans
    shade_polygons, shade_defs = shade.to.inp(shade)
    assert shade_defs[0] == \
       '"Awning 10" = FIXED-SHADE\n' \
       '   SHAPE                    = RECTANGLE\n' \
       '   HEIGHT                   = 2.0\n' \
       '   WIDTH                    = 2.0\n' \
       '   X-REF                    = 0.0\n' \
       '   Y-REF                    = 0.0\n' \
       '   Z-REF                    = 4.0\n' \
       '   TILT                     = 0.0\n' \
       '   AZIMUTH                  = 180.0\n' \
       '   TRANSMITTANCE            = 0.5\n' \
       '   ..\n'


def test_aperture_writer():
    """Test the basic functionality of the Aperture inp writer."""
    vertices_parent_wall = [[0, 0, 0], [0, 10, 0], [0, 10, 3], [0, 0, 3]]
    vertices_parent_wall_2 = list(reversed(vertices_parent_wall))
    vertices_wall = [[0, 1, 1], [0, 3, 1], [0, 3, 2.5], [0, 1, 2.5]]
    vertices_wall_2 = list(reversed(vertices_wall))
    vertices_parent_roof = [[10, 0, 3], [10, 10, 3], [0, 10, 3], [0, 0, 3]]
    vertices_roof = [[4, 1, 3], [4, 4, 3], [1, 4, 3], [1, 1, 3]]

    wf = Face.from_vertices('wall_face', vertices_parent_wall)
    wa = Aperture.from_vertices('wall_window', vertices_wall)
    wf.add_aperture(wa)
    Room('Test_Room_1', [wf])
    assert wa.properties.energy.construction.identifier == 'Generic Double Pane'
    inp_str = wa.to.inp(wa)
    assert inp_str == \
       '"wall window" = WINDOW\n' \
       '   X                        = 1.0\n' \
       '   Y                        = 1.0\n' \
       '   WIDTH                    = 2.0\n' \
       '   HEIGHT                   = 1.5\n' \
       '   GLASS-TYPE               = "Generic Double Pane"\n' \
       '   ..\n'

    wf2 = Face.from_vertices('wall_face2', vertices_parent_wall_2)
    wa2 = Aperture.from_vertices('wall_window2', vertices_wall_2)
    wf2.add_aperture(wa2)
    Room('Test_Room_2', [wf2])
    wa.set_adjacency(wa2)
    assert wa.properties.energy.construction.identifier == 'Generic Single Pane'
    inp_str = wa.to.inp(wa)
    assert inp_str == \
       '"wall window" = WINDOW\n' \
       '   X                        = 1.0\n' \
       '   Y                        = 1.0\n' \
       '   WIDTH                    = 2.0\n' \
       '   HEIGHT                   = 1.5\n' \
       '   GLASS-TYPE               = "Generic Single Pane"\n' \
       '   ..\n'

    rf = Face.from_vertices('roof_face', vertices_parent_roof)
    ra = Aperture.from_vertices('roof_window', vertices_roof)
    rf.add_aperture(ra)
    Room('Test_Room_1', [rf])
    assert ra.properties.energy.construction.identifier == 'Generic Double Pane'
    inp_str = ra.to.inp(ra)
    assert inp_str == \
       '"roof window" = WINDOW\n' \
       '   X                        = 1.0\n' \
       '   Y                        = 1.0\n' \
       '   WIDTH                    = 3.0\n' \
       '   HEIGHT                   = 3.0\n' \
       '   GLASS-TYPE               = "Generic Double Pane"\n' \
       '   ..\n'


def test_door_writer():
    """Test the basic functionality of the Door inp writer."""
    vertices_parent_wall = [[0, 0, 0], [0, 10, 0], [0, 10, 3], [0, 0, 3]]
    vertices_wall = [[0, 1, 0.1], [0, 2, 0.1], [0, 2, 2.8], [0, 1, 2.8]]
    vertices_parent_roof = [[10, 0, 3], [10, 10, 3], [0, 10, 3], [0, 0, 3]]
    vertices_roof = [[4, 3, 3], [4, 4, 3], [3, 4, 3], [3, 3, 3]]

    wf = Face.from_vertices('wall_face', vertices_parent_wall)
    wd = Door.from_vertices('wall_door', vertices_wall)
    wf.add_door(wd)
    Room('Test_Room_1', [wf])
    assert wd.properties.energy.construction.identifier == 'Generic Exterior Door'
    inp_str = wd.to.inp(wd)
    assert inp_str == \
       '"wall door" = DOOR\n' \
       '   X                        = 1.0\n' \
       '   Y                        = 0.1\n' \
       '   WIDTH                    = 1.0\n' \
       '   HEIGHT                   = 2.7\n' \
       '   CONSTRUCTION             = "Generic Exterior Door"\n' \
       '   ..\n'

    rf = Face.from_vertices('roof_face', vertices_parent_roof)
    rd = Door.from_vertices('roof_door', vertices_roof)
    rf.add_door(rd)
    Room('Test_Room_1', [rf])
    assert rd.properties.energy.construction.identifier == 'Generic Exterior Door'
    inp_str = rd.to.inp(rd)
    assert inp_str == \
       '"roof door" = DOOR\n' \
       '   X                        = 3.0\n' \
       '   Y                        = 3.0\n' \
       '   WIDTH                    = 1.0\n' \
       '   HEIGHT                   = 1.0\n' \
       '   CONSTRUCTION             = "Generic Exterior Door"\n' \
       '   ..\n'


def test_face_writer():
    """Test the basic functionality of the Face inp writer."""
    concrete20 = EnergyMaterial('20cm Concrete', 0.2, 2.31, 2322, 832,
                                'MediumRough', 0.95, 0.75, 0.8)
    thick_constr = OpaqueConstruction(
        'Thick Concrete Construction', [concrete20])

    wall_pts = [[0, 0, 0], [10, 0, 0], [10, 0, 10], [0, 0, 10]]
    roof_pts = [[0, 0, 3], [10, 0, 3], [10, 10, 3], [0, 10, 3]]
    floor_pts = [[0, 0, 0], [0, 10, 0], [10, 10, 0], [10, 0, 0]]

    face = Face.from_vertices('wall_face', wall_pts)
    face.properties.energy.construction = thick_constr
    face_polygon, face_def = face.to.inp(face)
    assert face_polygon == \
       '"wall face Plg" = POLYGON\n' \
       '   V1                       = (0.0, 0.0)\n' \
       '   V2                       = (10.0, 0.0)\n' \
       '   V3                       = (10.0, 10.0)\n' \
       '   V4                       = (0.0, 10.0)\n' \
       '   ..\n'
    assert face_def == \
       '"wall face" = EXTERIOR-WALL\n' \
       '   POLYGON                  = "wall face Plg"\n' \
       '   CONSTRUCTION             = "Thick Concrete Construction"\n' \
       '   TILT                     = 90.0\n' \
       '   AZIMUTH                  = 180.0\n' \
       '   X                        = 0.0\n' \
       '   Y                        = 0.0\n' \
       '   Z                        = 0.0\n' \
       '   ..\n'

    face = Face.from_vertices('roof_face', roof_pts)
    face.properties.energy.construction = thick_constr
    face_polygon, face_def = face.to.inp(face)
    assert face_polygon == \
       '"roof face Plg" = POLYGON\n' \
       '   V1                       = (0.0, 0.0)\n' \
       '   V2                       = (10.0, 0.0)\n' \
       '   V3                       = (10.0, 10.0)\n' \
       '   V4                       = (0.0, 10.0)\n' \
       '   ..\n'
    assert face_def == \
       '"roof face" = ROOF\n' \
       '   POLYGON                  = "roof face Plg"\n' \
       '   CONSTRUCTION             = "Thick Concrete Construction"\n' \
       '   TILT                     = 0.0\n' \
       '   AZIMUTH                  = 180.0\n' \
       '   X                        = 0.0\n' \
       '   Y                        = 0.0\n' \
       '   Z                        = 3.0\n' \
       '   ..\n'
    
    face = Face.from_vertices('floor_face', floor_pts)
    face.properties.energy.construction = thick_constr
    face_polygon, face_def = face.to.inp(face)
    assert face_polygon == \
       '"floor face Plg" = POLYGON\n' \
       '   V1                       = (0.0, 0.0)\n' \
       '   V2                       = (-10.0, 0.0)\n' \
       '   V3                       = (-10.0, -10.0)\n' \
       '   V4                       = (0.0, -10.0)\n' \
       '   ..\n'
    assert face_def == \
       '"floor face" = UNDERGROUND-WALL\n' \
       '   POLYGON                  = "floor face Plg"\n' \
       '   CONSTRUCTION             = "Thick Concrete Construction"\n' \
       '   TILT                     = 180.0\n' \
       '   AZIMUTH                  = 180.0\n' \
       '   X                        = 10.0\n' \
       '   Y                        = 0.0\n' \
       '   Z                        = 0.0\n' \
       '   LOCATION                 = BOTTOM\n' \
       '   ..\n'


def test_room_writer():
    """Test the basic functionality of the Room inp writer."""
    room = Room.from_box('Tiny_House_Zone', 15, 30, 10)
    south_face = room[3]
    south_face.apertures_by_ratio(0.4, 0.01)
    south_face.apertures[0].overhang(0.5, indoor=False)
    south_face.apertures[0].overhang(0.5, indoor=True)
    south_face.apertures[0].move_shades(Vector3D(0, 0, -0.5))

    room_polygons, room_def = room.to.inp(room)
    assert room_polygons[0] == \
       '"Tiny House Zone Plg" = POLYGON\n' \
       '   V1                       = (0.0, 0.0)\n' \
       '   V2                       = (15.0, 0.0)\n' \
       '   V3                       = (15.0, 30.0)\n' \
       '   V4                       = (0.0, 30.0)\n' \
       '   ..\n'
    assert room_def[0] == \
       '"Tiny House Zone" = SPACE\n' \
       '   SHAPE                    = POLYGON\n' \
       '   POLYGON                  = "Tiny House Zone Plg"\n' \
       '   AZIMUTH                  = 0\n' \
       '   X                        = 0.0\n' \
       '   Y                        = 0.0\n' \
       '   Z                        = 0.0\n' \
       '   VOLUME                   = 4500\n' \
       '   ZONE-TYPE                = UNCONDITIONED\n' \
       '   ..\n'

    room.properties.energy.program_type = office_program
    room.properties.energy.add_default_ideal_air()
    room_polygons, room_def = room.to.inp(room)
    assert room_polygons[0] == \
       '"Tiny House Zone Plg" = POLYGON\n' \
       '   V1                       = (0.0, 0.0)\n' \
       '   V2                       = (15.0, 0.0)\n' \
       '   V3                       = (15.0, 30.0)\n' \
       '   V4                       = (0.0, 30.0)\n' \
       '   ..\n'
    assert room_def[0] == \
       '"Tiny House Zone" = SPACE\n' \
       '   SHAPE                    = POLYGON\n' \
       '   POLYGON                  = "Tiny House Zone Plg"\n' \
       '   AZIMUTH                  = 0\n' \
       '   X                        = 0.0\n' \
       '   Y                        = 0.0\n' \
       '   Z                        = 0.0\n' \
       '   VOLUME                   = 4500\n' \
       '   ZONE-TYPE                = CONDITIONED\n' \
       '   C-ACTIVITY-DESC          = *Generic_Office_Program*\n' \
       '   ..\n'

    room.properties.energy.program_type = None
    room.properties.energy.people = office_program.people
    room.properties.energy.lighting = office_program.lighting
    room.properties.energy.electric_equipment = office_program.electric_equipment
    room.properties.energy.infiltration = office_program.infiltration
    room.properties.energy.ventilation = office_program.ventilation
    room.properties.energy.setpoint = office_program.setpoint
    room_polygons, room_def = room.to.inp(room)
    assert room_def[0] == \
       '"Tiny House Zone" = SPACE\n' \
       '   SHAPE                    = POLYGON\n' \
       '   POLYGON                  = "Tiny House Zone Plg"\n' \
       '   AZIMUTH                  = 0\n' \
       '   X                        = 0.0\n' \
       '   Y                        = 0.0\n' \
       '   Z                        = 0.0\n' \
       '   VOLUME                   = 4500\n' \
       '   ZONE-TYPE                = CONDITIONED\n' \
       '   AREA/PERSON              = 190.512\n' \
       '   PEOPLE-SCHEDULE          = "Generic Office Occupancy"\n' \
       '   LIGHTING-W/AREA          = 0.98\n' \
       '   LIGHTING-SCHEDULE        = "Generic Office Lighting"\n' \
       '   LIGHT-TO-RETURN          = 0.0\n' \
       '   EQUIPMENT-W/AREA         = 0.96\n' \
       '   EQUIP-SCHEDULE           = ("Generic Office Equipment")\n' \
       '   EQUIP-SENSIBLE           = 1.0\n' \
       '   EQUIP-LATENT             = 0.0\n' \
       '   EQUIP-RAD-FRAC           = 0.5\n' \
       '   INF-METHOD               = AIR-CHANGE\n' \
       '   INF-FLOW/AREA            = 0.045\n' \
       '   INF-SCHEDULE             = "Generic Office Infiltration"\n' \
       '   ..\n'


def test_room_writer_program():
    """Test the the Room inp writer with different types of programs."""
    room = Room.from_box('Tiny_House_Zone', 15, 30, 10)
    south_face = room[3]
    south_face.apertures_by_ratio(0.4, 0.01)

    apartment_prog = program_type_by_identifier('2019::MidriseApartment::Apartment')
    room.properties.energy.add_default_ideal_air()
    room.properties.energy.people = apartment_prog.people
    room.properties.energy.lighting = apartment_prog.lighting
    room.properties.energy.electric_equipment = apartment_prog.electric_equipment
    room.properties.energy.service_hot_water = apartment_prog.service_hot_water
    room.properties.energy.infiltration = apartment_prog.infiltration
    room.properties.energy.ventilation = apartment_prog.ventilation
    room.properties.energy.setpoint = apartment_prog.setpoint
    _, room_def = room.to.inp(room)
    assert room_def[0] == \
       '"Tiny House Zone" = SPACE\n' \
       '   SHAPE                    = POLYGON\n' \
       '   POLYGON                  = "Tiny House Zone Plg"\n' \
       '   AZIMUTH                  = 0\n' \
       '   X                        = 0.0\n' \
       '   Y                        = 0.0\n' \
       '   Z                        = 0.0\n' \
       '   VOLUME                   = 4500\n' \
       '   ZONE-TYPE                = CONDITIONED\n' \
       '   AREA/PERSON              = 380.228\n' \
       '   PEOPLE-SCHEDULE          = "ApartmentMidRise OCC APT SCH"\n' \
       '   LIGHTING-W/AREA          = 0.87\n' \
       '   LIGHTING-SCHEDULE        = "ApartmentMidRise LTG APT SCH"\n' \
       '   LIGHT-TO-RETURN          = 0.0\n' \
       '   EQUIPMENT-W/AREA         = 0.62\n' \
       '   EQUIP-SCHEDULE           = ("ApartmentMidRise EQP APT SCH")\n' \
       '   EQUIP-SENSIBLE           = 1.0\n' \
       '   EQUIP-LATENT             = 0.0\n' \
       '   EQUIP-RAD-FRAC           = 0.5\n' \
       '   SOURCE-TYPE              = HOT-WATER\n' \
       '   SOURCE-POWER             = 1.238\n' \
       '   SOURCE-SCHEDULE          = "ApartmentMidRise APT DHW SCH"\n' \
       '   SOURCE-SENSIBLE          = 0.2\n' \
       '   SOURCE-RAD-FRAC          = 0\n' \
       '   SOURCE-LATENT            = 0.05\n' \
       '   INF-METHOD               = AIR-CHANGE\n' \
       '   INF-FLOW/AREA            = 0.112\n' \
       '   INF-SCHEDULE             = "ApartmentMidRise INF APT SCH"\n' \
       '   ..\n'

    kitchen_prog = program_type_by_identifier('2019::FullServiceRestaurant::Kitchen')
    room.properties.energy.people = kitchen_prog.people
    room.properties.energy.lighting = kitchen_prog.lighting
    room.properties.energy.electric_equipment = kitchen_prog.electric_equipment
    room.properties.energy.gas_equipment = kitchen_prog.gas_equipment
    room.properties.energy.service_hot_water = kitchen_prog.service_hot_water
    room.properties.energy.infiltration = kitchen_prog.infiltration
    room.properties.energy.ventilation = kitchen_prog.ventilation
    room.properties.energy.setpoint = kitchen_prog.setpoint
    _, room_def = room.to.inp(room)
    assert room_def[0] == \
       '"Tiny House Zone" = SPACE\n' \
       '   SHAPE                    = POLYGON\n' \
       '   POLYGON                  = "Tiny House Zone Plg"\n' \
       '   AZIMUTH                  = 0\n' \
       '   X                        = 0.0\n' \
       '   Y                        = 0.0\n' \
       '   Z                        = 0.0\n' \
       '   VOLUME                   = 4500\n' \
       '   ZONE-TYPE                = CONDITIONED\n' \
       '   AREA/PERSON              = 200.0\n' \
       '   PEOPLE-SCHEDULE          = "RestaurantSitDown BLDG OCC SCH"\n' \
       '   LIGHTING-W/AREA          = 1.09\n' \
       '   LIGHTING-SCHEDULE        = "RstrntStDwnBLDG_HENSCH20102013"\n' \
       '   LIGHT-TO-RETURN          = 0.0\n' \
       '   EQUIPMENT-W/AREA         = (37.53, 60.317)\n' \
       '   EQUIP-SCHEDULE           = ("RstrntStDwn BLDG EQUIP SCH",\n' \
       '                               "RstrntStDwn Rst GAS EQUIP SCH")\n' \
       '   EQUIP-SENSIBLE           = (0.55, 0.2)\n' \
       '   EQUIP-LATENT             = (0.25, 0.1)\n' \
       '   EQUIP-RAD-FRAC           = (0.3, 0.2)\n' \
       '   SOURCE-TYPE              = HOT-WATER\n' \
       '   SOURCE-POWER             = 29.943\n' \
       '   SOURCE-SCHEDULE          = "RestaurantSitDown BLDG SWH SCH"\n' \
       '   SOURCE-SENSIBLE          = 0.2\n' \
       '   SOURCE-RAD-FRAC          = 0\n' \
       '   SOURCE-LATENT            = 0.05\n' \
       '   INF-METHOD               = AIR-CHANGE\n' \
       '   INF-FLOW/AREA            = 0.112\n' \
       '   INF-SCHEDULE             = "RstrntStDwn INFIL HALF ON SCH"\n' \
       '   ..\n'


def test_model_writer():
    """Test the basic functionality of the Model inp writer."""
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

    inp_str = model.to.inp(model)
    assert inp_str.startswith('INPUT ..\n\n')
    assert inp_str.endswith('END ..\nCOMPUTE ..\nSTOP ..\n')


def test_model_writer_from_standard_hbjson():
    """Test translating a HBJSON to an INP string."""
    standard_test = './tests/assets/2023_rac_advanced_sample_project.hbjson'
    hb_model = Model.from_file(standard_test)

    inp_str = hb_model.to.inp(hb_model, hvac_mapping='Model')
    assert inp_str.startswith('INPUT ..\n\n')
    assert inp_str.endswith('END ..\nCOMPUTE ..\nSTOP ..\n')


def test_model_writer_from_hvac_hbjson():
    """Test translating a HBJSON to an INP string."""
    hvac_test = './tests/assets/multi_hvac.hbjson'
    hb_model = Model.from_file(hvac_test)

    inp_str = hb_model.to.inp(hb_model, hvac_mapping='AssignedHVAC')
    assert inp_str.startswith('INPUT ..\n\n')
    assert inp_str.endswith('END ..\nCOMPUTE ..\nSTOP ..\n')


def test_model_writer_from_air_wall_hbjson():
    """Test translating a HBJSON to an INP string."""
    air_wall_test = './tests/assets/Air_Wall_test.hbjson'
    hb_model = Model.from_file(air_wall_test)

    inp_str = hb_model.to.inp(hb_model, hvac_mapping='Room')
    assert inp_str.startswith('INPUT ..\n\n')
    assert inp_str.endswith('END ..\nCOMPUTE ..\nSTOP ..\n')


def test_model_writer_from_ceil_adj_hbjson():
    """Test translating a HBJSON to an INP string."""
    ceiling_adj_test = './tests/assets/ceiling_adj_test.hbjson'
    hb_model = Model.from_file(ceiling_adj_test)

    inp_str = hb_model.to.inp(hb_model, hvac_mapping='AssignedHVAC')
    assert inp_str.startswith('INPUT ..\n\n')
    assert inp_str.endswith('END ..\nCOMPUTE ..\nSTOP ..\n')

    
