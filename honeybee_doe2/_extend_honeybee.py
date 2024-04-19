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

# TODO: Extend classes of honeybee-energy with to_inp() methods and inp_identifier()
