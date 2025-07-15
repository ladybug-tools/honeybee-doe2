"""Test the reader functions."""
import os
from honeybee_doe2.reader import command_dict_from_inp, model_from_inp
from honeybee.model import Model

def log_face_normals(model):
    print("FACE NORMAL CHECK (metres, model coords)")
    for room in model.rooms:
        for face in room.faces:
            boundary = face.geometry.boundary
            if len(boundary) < 3:
                continue  # Degenerate face
            a = boundary[0]
            b = boundary[1]
            c = boundary[2]
            # Compute vectors AB and AC
            ab = [b[i] - a[i] for i in range(3)]
            ac = [c[i] - a[i] for i in range(3)]
            # Compute cross product AB × AC
            nx = ab[1] * ac[2] - ab[2] * ac[1]
            ny = ab[2] * ac[0] - ab[0] * ac[2]
            nz = ab[0] * ac[1] - ab[1] * ac[0]
            length = math.sqrt(nx * nx + ny * ny + nz * nz)
            if length < 1e-9:
                continue  # Degenerate normal
            # Normalize the normal vector
            nx /= length
            ny /= length
            nz /= length
            print(f"· {face.identifier:<25}  n=({nx:.3f}, {ny:.3f}, {nz:.3f})")

def log_model_summary(model):
    print(f"HB-MODEL SUMMARY  ({len(model.rooms)} rooms)")
    for room in model.rooms:
        faces = room.faces
        print(f"- Room {room.identifier}  |  Faces:{len(faces)}")
        for face in faces:
            bc = face.boundary_condition.name if face.boundary_condition else "null"
            verts = face.geometry.boundary
            print(f"   · {face.identifier:<25}  BC:{bc:<10} verts:{len(verts)}")
            for i, v in enumerate(verts):
                print(f"       v{i}: ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})")
    print("---- end summary ----")

def test_parse_inp_file():
    """Test parsing of a DOE-2 INP file into object dict"""
    #inp_file_path = './tests/assets/test_project.inp'
    inp_file_path = os.path.join(os.path.dirname(__file__), 'assets', 'test_project.inp')
    with open(inp_file_path, 'r') as doe_file:
        inp_content = doe_file.read()
    inp_object_dict = command_dict_from_inp(inp_content)

    assert isinstance(inp_object_dict, dict)
    assert 'PARAMETER' in inp_object_dict or len(inp_object_dict) > 0

    assert 'SPACE' in inp_object_dict
    assert isinstance(inp_object_dict['SPACE'], dict)
    assert len(inp_object_dict['SPACE']) > 0

    known_space = 'L1WNE Perim Spc (G.NE1)'
    assert known_space in inp_object_dict['SPACE']

    space_obj = inp_object_dict['SPACE'][known_space]
    assert isinstance(space_obj, dict)


inp_file_path = os.path.join(os.path.dirname(__file__), 'assets', 'sloped_roof_from_wiz.inp')
model = model_from_inp(inp_file_path)

model.to_hbjson(r'C:\Users\Steve.marentette.IG\Desktop\doe\out.hbjson')

#log_model_summary(model)
