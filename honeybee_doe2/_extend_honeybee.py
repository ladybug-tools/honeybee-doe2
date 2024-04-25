# coding=utf-8
# import all of the modules for writing geometry to INP
import honeybee.writer.shademesh as shade_mesh_writer
import honeybee.writer.door as door_writer
import honeybee.writer.aperture as aperture_writer
import honeybee.writer.shade as shade_writer
import honeybee.writer.face as face_writer
import honeybee.writer.room as room_writer
import honeybee.writer.model as model_writer
from .writer import model_to_inp, room_to_inp, face_to_inp, shade_to_inp, \
    aperture_to_inp, door_to_inp, shade_mesh_to_inp

# add writers to the honeybee-core modules
model_writer.inp = model_to_inp
room_writer.inp = room_to_inp
face_writer.inp = face_to_inp
shade_writer.inp = shade_to_inp
aperture_writer.inp = aperture_to_inp
door_writer.inp = door_to_inp
shade_mesh_writer.inp = shade_mesh_to_inp


# import the modules that extend honeybee-energy objects
from honeybee_energy.schedule.day import ScheduleDay
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.material.opaque import EnergyMaterial, EnergyMaterialNoMass, \
    EnergyMaterialVegetation
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.construction.windowshade import WindowConstructionShade
from honeybee_energy.construction.dynamic import WindowConstructionDynamic
from honeybee_energy.construction.air import AirBoundaryConstruction
from honeybee_energy.simulation.runperiod import RunPeriod

from .schedule import schedule_day_to_inp, schedule_ruleset_to_inp
from .construction import opaque_material_to_inp, opaque_construction_to_inp, \
    window_construction_to_inp, air_construction_to_inp
from .simulation import run_period_to_inp

# add the methods to the honeybee-energy classes
ScheduleDay.to_inp = schedule_day_to_inp
ScheduleRuleset.to_inp = schedule_ruleset_to_inp
EnergyMaterial.to_inp = opaque_material_to_inp
EnergyMaterialNoMass.to_inp = opaque_material_to_inp
EnergyMaterialVegetation.to_inp = opaque_material_to_inp
OpaqueConstruction.to_inp = opaque_construction_to_inp
WindowConstruction.to_inp = window_construction_to_inp
WindowConstructionShade.to_inp = window_construction_to_inp
WindowConstructionDynamic.to_inp = window_construction_to_inp
AirBoundaryConstruction.to_inp = air_construction_to_inp
RunPeriod.to_inp = run_period_to_inp
