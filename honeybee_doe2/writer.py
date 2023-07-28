import pathlib

from .properties.inputils import blocks as fb
from .properties.inputils.compliance import ComplianceData
from .properties.inputils.sitebldg import SiteBldgData as sbd
from .properties.inputils.run_period import RunPeriod
from .properties.inputils.title import Title
from .properties.inputils.glass_types import GlassType
from .utils.doe_formatters import short_name

from honeybee.model import Model
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.lib.constructionsets import generic_construction_set
from honeybee.boundarycondition import Surface
from honeybee.typing import clean_and_id_string


def model_to_inp(hb_model):
    # type: (Model) -> str
    rp = RunPeriod()
    comp_data = ComplianceData()
    sb_data = sbd()

    hb_model = hb_model.duplicate()

    if hb_model.units != 'Feet':
        hb_model.convert_to_units(units='Feet')
    hb_model.remove_degenerate_geometry()
    hb_model.rectangularize_apertures(subdivision_distance=0.5, max_separation=0)

    room_names = {}
    face_names = {}
    for room in hb_model.rooms:
        room.display_name = room.display_name.replace('..', '_')
        if room.display_name in room_names:
            original_name = room.display_name
            room.display_name = f'{original_name}_{room_names[original_name]}'
            room_names[original_name] += 1
        else:
            room_names[room.display_name] = 1

        for face in room.faces:
            face.display_name = face.display_name.replace('..', '_')
            if face.display_name in face_names:
                original_name = face.display_name
                face.display_name = f'{original_name}_{face_names[original_name]}'
                face_names[original_name] += 1
            else:
                face_names[face.display_name] = 1

            for apt in face.apertures:
                apt.display_name = apt.display_name.replace('..', '_')
                if apt.display_name in face_names:
                    original_name = apt.display_name
                    apt.display_name = f'{original_name}_{face_names[original_name]}'
                    face_names[original_name] += 1
                else:
                    face_names[face.display_name] = 1

    room_mapper = {
        r.identifier: r.display_name for r in hb_model.rooms
    }
    for i, shade in enumerate(hb_model.shades):
        shade.display_name = f'shade_{i}'
    for face in hb_model.faces:
        if isinstance(face.boundary_condition, Surface):
            adj_room_identifier = face.boundary_condition.boundary_condition_objects[1]
            face.user_data = {'adjacent_room': room_mapper[adj_room_identifier]}

    for i, room in enumerate(hb_model.rooms):
        for face in room.faces:
            try:
                _ = face.horizontal_orientation()
            except ZeroDivisionError:
                face.display_name = short_name(
                    clean_and_id_string(face.display_name)).replace(
                    '..', '_')
            else:
                face.display_name = short_name(
                    clean_and_id_string(face.display_name)).replace(
                    '..', '_')

            for ap in face.apertures:
                ap.display_name = short_name(
                    clean_and_id_string(ap.display_name)).replace(
                    '..', '_')

    window_constructions = [generic_construction_set.aperture_set.window_construction]

    for construction in hb_model.properties.energy.constructions:
        if isinstance(construction, WindowConstruction):
            window_constructions.append(construction)
    wind_con_set = set(window_constructions)
    win_con_to_inp = [GlassType.from_hb_window_constr(constr) for constr in wind_con_set]

    data = [
        hb_model.properties.doe2._header,
        fb.global_params,
        fb.ttrpddh,
        Title(title=str(hb_model.display_name)).to_inp(),
        rp.to_inp(),  # TODO unhardcode
        fb.comply,
        comp_data.to_inp(),
        sb_data.to_inp(),
        fb.mats_layers,
        hb_model.properties.doe2.mats_cons_layers,
        fb.glzCode,
        '\n'.join(gt.to_inp() for gt in win_con_to_inp),
        fb.polygons,
        '\n'.join(s.story_poly for s in hb_model.properties.doe2.stories),
        fb.wallParams,
        hb_model.properties.doe2.fixed_shades,
        fb.miscCost,
        fb.perfCurve,
        fb.floorNspace,
        '\n'.join(str(story) for story in hb_model.properties.doe2.stories),
        fb.elecFuelMeter,
        fb.elec_meter,
        fb.fuel_meter,
        fb.master_meter,
        fb.hvac_circ_loop,
        fb.pumps,
        fb.heat_exch,
        fb.circ_loop,
        fb.chiller_objs,
        fb.boiler_objs,
        fb.dwh,
        fb.heat_reject,
        fb.tower_free,
        fb.pvmod,
        fb.elecgen,
        fb.thermal_store,
        fb.ground_loop_hx,
        fb.comp_dhw_res,
        fb.steam_cld_mtr,
        fb.steam_mtr,
        fb.chill_meter,
        fb.hvac_sys_zone,
        '\n'.join(hv_sys.to_inp()
                  for hv_sys in hb_model.properties.doe2.hvac_sys_zones),  # TODO need to frame up hvac
        fb.misc_meter_hvac,
        fb.equip_controls,
        fb.load_manage,
        fb.big_util_rate,
        fb.ratchets,
        fb.block_charge,
        fb.small_util_rate,
        fb.output_reporting,
        fb.loads_non_hrly,
        fb.sys_non_hrly,
        fb.plant_non_hrly,
        fb.econ_non_hrly,
        fb.hourly_rep,
        fb.the_end
    ]
    return str('\n\n'.join(data))


def honeybee_model_to_inp(
        model: Model, folder: str = '.', name: str = None) -> pathlib.Path:

    inp_model = model_to_inp(model)

    name = name or model.display_name
    if not name.lower().endswith('.inp'):
        name = f'{name}.inp'
    out_folder = pathlib.Path(folder)
    out_folder.mkdir(parents=True, exist_ok=True)
    out_file = out_folder.joinpath(name)
    out_file.write_text(inp_model)
    return out_file
