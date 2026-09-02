"""honeybee-doe2 translation commands."""
import sys
import json
import logging
import click

from ladybug.commandutil import process_content_to_output
from honeybee.typing import clean_doe2_string
from honeybee.model import Model
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.schedule.dictutil import dict_to_schedule
from honeybee_energy.material.opaque import _EnergyMaterialOpaqueBase
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.air import AirBoundaryConstruction
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.construction.dictutil import dict_to_construction

from honeybee_doe2.config import RES_CHARS
from honeybee_doe2.util import header_comment_minor
from honeybee_doe2.schedule import extract_all_schedule_ruleset_from_inp_file
from honeybee_doe2.construction import opaque_material_to_inp, opaque_construction_to_inp, \
    window_construction_to_inp, air_construction_to_inp, \
    extract_all_constructions_from_inp_file
from honeybee_doe2.simulation import SimulationPar
from honeybee_doe2.reader import model_from_inp_file

_logger = logging.getLogger(__name__)


@click.group(help='Commands for translating Honeybee Model to DOE-2 formats.')
def translate():
    pass


@translate.command('model-to-inp')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option(
    '--sim-par-json', '-sp', help='Full path to a honeybee-doe2 SimulationPar '
    'JSON that describes all of the settings for the simulation. If unspecified, '
    'default parameters will be generated.', default=None, show_default=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option(
    '--hvac-mapping', '-hm', help='Text to indicate how HVAC systems should be '
    'assigned to the exported model. Story will assign one HVAC system for each '
    'distinct level polygon, Model will use only one HVAC system for the whole model '
    'and AssignedHVAC will follow how the HVAC systems have been assigned to the'
    'Rooms.properties.energy.hvac. Choose from: Room, Story, Model, AssignedHVAC',
    default='Story', show_default=True, type=str)
@click.option(
    '--include-interior-walls/--exclude-interior-walls', ' /-xw', help='Flag to note '
    'whether interior walls should be excluded from the export.',
    default=True, show_default=True)
@click.option(
    '--include-interior-ceilings/--exclude-interior-ceilings', ' /-xc', help='Flag to '
    'note whether interior ceilings should be excluded from the export.',
    default=True, show_default=True)
@click.option(
    '--equest-version', '-eq', help='Optional text string to denote the version '
    'of eQuest for which the INP definition will be generated. If unspecified '
    'or unrecognized, the latest version of eQuest will be used.',
    default='3.65', show_default=True, type=str)
@click.option(
    '--output-file', '-o', help='Optional INP file path to output the INP string '
    'of the translation. By default this will be printed out to stdout.',
    type=click.File('w'), default='-', show_default=True)
def model_to_inp_cli(
    model_file, sim_par_json, hvac_mapping, include_interior_walls,
    include_interior_ceilings, equest_version, output_file
):
    """Translate a Honeybee Model to an INP file.

    \b
    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
    """
    try:
        exclude_interior_walls = not include_interior_walls
        exclude_interior_ceilings = not include_interior_ceilings
        model_to_inp(
            model_file, sim_par_json, hvac_mapping,
            exclude_interior_walls, exclude_interior_ceilings,
            equest_version, output_file)
    except Exception as e:
        _logger.exception(f'Model translation failed:\n{e}')
        sys.exit(1)
    else:
        sys.exit(0)


def model_to_inp(
        model_file, sim_par_json=None, hvac_mapping='Story',
        exclude_interior_walls=False, exclude_interior_ceilings=False,
        equest_version='3.65', output_file=None,
        include_interior_walls=True, include_interior_ceilings=True):
    """Translate a Honeybee Model to an INP file.

    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
        sim_par_json: Full path to a honeybee-doe2 SimulationPar JSON that
            describes all of the settings for the simulation. If None,
            default parameters will be generated. (Default: None).
        hvac_mapping: Text to indicate how HVAC systems should be assigned to
            the exported model. Story will assign one HVAC system for each distinct
            level polygon, Model will use only one HVAC system for the whole model
            and AssignedHVAC will follow how the HVAC systems have been assigned
            to the Rooms.properties.energy.hvac. Choose from the following.

            * Room
            * Story
            * Model
            * AssignedHVAC

        exclude_interior_walls: Boolean to note whether interior walls should
            be excluded from the export. (Default: False).
        exclude_interior_ceilings: Boolean to note whether interior ceilings
            should be excluded from the export. (Default: False).
        equest_version: Optional text string to denote the version of eQuest for
            which the INP definition will be generated. If unspecified or
            unrecognized, the latest version of eQuest will be used. (Default: False).
        output_file: Optional INP file path to output the INP string of the
            translation. If None, the string will be returned from this function.
    """
    # load simulation parameters if specified
    sim_par = None
    if sim_par_json is not None:
        with open(sim_par_json) as json_file:
            data = json.load(json_file)
        sim_par = SimulationPar.from_dict(data)

    # re-serialize the Model to Python
    model = Model.from_file(model_file)

    # create the strings for the model
    inp_str = model.to.inp(
        model, sim_par, hvac_mapping,
        exclude_interior_walls, exclude_interior_ceilings, equest_version)

    # write out the INP file
    return process_content_to_output(inp_str, output_file)


@translate.command('model-from-inp')
@click.argument('inp-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option(
    '--output-file', '-o', help='Optional HBJSON file path to output the file string '
    'of the translation. By default this will be printed out to stdout.',
    type=click.File('w'), default='-', show_default=True)
def model_from_inp_cli(inp_file, output_file):
    """Translate an INP file to a Honeybee Model as a HBJSON.

    \b
    Args:
        inp_file: Full path to an INP file.
    """
    try:
        model_from_inp(inp_file, output_file)
    except Exception as e:
        _logger.exception(f'Model translation failed:\n{e}')
        sys.exit(1)
    else:
        sys.exit(0)


def model_from_inp(inp_file, output_file=None):
    """Translate an INP file to a Honeybee Model as a HBJSON.

    Args:
        inp_file: Full path to an INP file.
        output_file: Optional HBJSON file path to output the string of the
            translation. If None, the string will be returned from this function.
    """
    hb_model = model_from_inp_file(inp_file)
    content_str = json.dumps(hb_model.to_dict())
    return process_content_to_output(content_str, output_file)


@translate.command('schedules-to-inp')
@click.argument('schedule-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--output-file', '-f', help='Optional INP file to output the INP '
              'string of the translation. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def schedules_to_inp_cli(schedule_json, output_file):
    """Translate a Schedule JSON file to an INP.

    \b
    Args:
        schedule_json: Full path to a Schedule JSON file. This file should
            either be an array of non-abridged Schedules or a dictionary where
            the values are non-abridged Schedules.
    """
    try:
        schedules_to_inp(schedule_json, output_file)
    except Exception as e:
        _logger.exception('Schedule translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def schedules_to_inp(schedule_json, output_file=None):
    """Translate a Schedule JSON file to an INP.

    Args:
        schedule_json: Full path to a Schedule JSON file. This file should
            either be an array of non-abridged Schedules or a dictionary where
            the values are non-abridged Schedules.
        output_file: Optional INP file path to output the INP string of the
            translation. If None, the string will be returned from this function.
    """
    # re-serialize the Schedule to Python
    with open(schedule_json) as json_file:
        data = json.load(json_file)
    sch_list = data.values() if isinstance(data, dict) else data
    sch_objs = [dict_to_schedule(sch) for sch in sch_list]
    type_objs = set()
    for sch in sch_objs:
        type_objs.add(sch.schedule_type_limit)

    # create the INP strings
    all_day_scheds, all_week_scheds, all_year_scheds = [], [], []
    used_day_sched_ids, used_day_count = {}, 1
    all_scheds = sch_objs
    for sched in all_scheds:
        if isinstance(sched, ScheduleRuleset):
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
            year_schedule, week_schedules, year_schedule = sched.to_inp()
            all_day_scheds.extend(day_scheds)
            all_week_scheds.extend(week_schedules)
            all_year_scheds.append(year_schedule)
    inp_str_list = ['INPUT ..\n\n']
    inp_str_list.append(header_comment_minor('Day Schedules'))
    inp_str_list.extend(all_day_scheds)
    inp_str_list.append(header_comment_minor('Week Schedules'))
    inp_str_list.extend(all_week_scheds)
    inp_str_list.append(header_comment_minor('Annual Schedules'))
    inp_str_list.extend(all_year_scheds)
    inp_str_list.append('END ..\nCOMPUTE ..\nSTOP ..\n')
    inp_str = '\n'.join(inp_str_list)

    # write out the INP file
    return process_content_to_output(inp_str, output_file)


@translate.command('schedules-from-inp')
@click.argument('schedule-inp', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option(
    '--dictionary/--array', ' /-a', help='Flag to note whether a the output JSON '
    'should be an array of schedule objects or whether it should be a dictionary '
    'where each key is the identifier of the schedule and each value is the '
    'schedule object. The dictionary format is the one used by honeybee-standards '
    'and is recommended when writing INP schedules into the user standards library.',
    default=True, show_default=True)
@click.option(
    '--indent', '-i', help='Optional integer to specify the indentation in '
    'the output JSON file. Specifying an value here can produce more read-able'
    ' JSONs.', type=int, default=None, show_default=True)
@click.option(
    '--output-file', '-f', help='Optional JSON file to output the JSON string of '
    'the translation. By default this will be printed out to stdout',
    type=click.File('w'), default='-', show_default=True)
def schedules_from_inp_cli(schedule_inp, dictionary, indent, output_file):
    """Translate all schedules in an INP file to a honeybee JSON.

    \b
    Args:
        schedule_inp: Full path to a Schedule INP file.
    """
    try:
        array = not dictionary
        schedules_from_inp(schedule_inp, array, indent, output_file)
    except Exception as e:
        _logger.exception('Schedule translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def schedules_from_inp(
    schedule_inp, array=False, indent=None, output_file=None, dictionary=True
):
    """Translate all schedules in an INP file to a honeybee JSON.

    Args:
        schedule_inp: Full path to a Schedule INP file.
        array: Boolean to note whether a the output JSON should be an array of
            schedule objects or whether it should be a dictionary where each key
            is the identifier of the schedule and each value is the schedule object.
            The dictionary format is the one used by honeybee-standards and is
            recommended when writing INP schedules into the user standards
            library. (Default: False).
        indent: Optional integer to specify the indentation in the output JSON file.
            Specifying an value here can produce more read-able JSONs. (Default: None).
        output_file: Optional JSON file path to output the JSON string of the
            translation. If None, the string will be returned from this function.
    """
    # re-serialize the schedules to Python
    schedules = extract_all_schedule_ruleset_from_inp_file(schedule_inp)
    # create the honeybee dictionaries
    if array:
        hb_objs = [sch.to_dict() for sch in schedules]
    else:
        hb_objs = {sch.identifier: sch.to_dict() for sch in schedules}
    # write out the JSON file
    content_str = json.dumps(hb_objs, indent=indent)
    return process_content_to_output(content_str, output_file)


@translate.command('constructions-to-inp')
@click.argument('construction-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--output-file', '-f', help='Optional INP file to output the INP string '
              'of the translation. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def constructions_to_inp_cli(construction_json, output_file):
    """Translate a Construction JSON file to an INP.

    \b
    Args:
        construction_json: Full path to a Construction JSON file. This file should
            either be an array of non-abridged Constructions or a dictionary where
            the values are non-abridged Constructions.
    """
    try:
        constructions_to_inp(construction_json, output_file)
    except Exception as e:
        _logger.exception('Construction translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def constructions_to_inp(construction_json, output_file=None):
    """Translate a Construction JSON file to an INP.

    Args:
        construction_json: Full path to a Construction JSON file. This file should
            either be an array of non-abridged Constructions or a dictionary where
            the values are non-abridged Constructions.
        output_file: Optional INP file to output the string of the translation.
            If None, it will be returned from this method. (Default: None).
    """
    # re-serialize the Constructions to Python
    with open(construction_json) as json_file:
        data = json.load(json_file)
    constr_list = data.values() if isinstance(data, dict) else data
    constr_objs = [dict_to_construction(constr) for constr in constr_list]
    materials = set()
    for constr in constr_objs:
        try:
            for mat in constr.materials:
                if isinstance(mat, _EnergyMaterialOpaqueBase):
                    materials.add(mat)
        except AttributeError:  # not a construction with materials
            pass

    # create the INP strings
    # write all of the materials and constructions
    window_constructions = []
    construction_strs = []
    for constr in set(constr_objs):
        if isinstance(constr, OpaqueConstruction):
            construction_strs.append(opaque_construction_to_inp(constr))
        elif isinstance(constr, AirBoundaryConstruction):
            construction_strs.append(air_construction_to_inp(constr))
        elif isinstance(constr, WindowConstruction):
            window_constructions.append(constr)

    inp_str_list = ['INPUT ..\n\n']
    inp_str_list.append(header_comment_minor('Materials / Layers / Constructions'))
    inp_str_list.extend([opaque_material_to_inp(mat) for mat in materials])
    inp_str_list.extend(construction_strs)
    inp_str_list.append(header_comment_minor('Glass Types'))
    for w_con in window_constructions:
        inp_str_list.append(window_construction_to_inp(w_con))
    inp_str_list.append('END ..\nCOMPUTE ..\nSTOP ..\n')
    inp_str = '\n'.join(inp_str_list)

    # write out the INP file
    return process_content_to_output(inp_str, output_file)


@translate.command('materials-from-inp')
@click.argument('material-inp', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option(
    '--dictionary/--array', ' /-a', help='Flag to note whether a the output JSON '
    'should be an array of objects or whether it should be a dictionary '
    'where each key is the identifier of the material and each value is the '
    'material object. The dictionary format is the one used by honeybee-standards '
    'and is recommended when writing INP constructions into the user standards library.',
    default=True, show_default=True)
@click.option(
    '--indent', '-i', help='Optional integer to specify the indentation in '
    'the output JSON file. Specifying an value here can produce more read-able'
    ' JSONs.', type=int, default=None, show_default=True)
@click.option(
    '--output-file', '-f', help='Optional JSON file to output the JSON '
    'string of the translation. By default this will be printed out to stdout',
    type=click.File('w'), default='-', show_default=True)
def materials_from_inp_cli(material_inp, dictionary, indent, output_file):
    """Translate all materials in an INP file to a honeybee JSON.

    \b
    Args:
        material_inp: Full path to an INP file. Only the materials in this file
            will be extracted.
    """
    try:
        array = not dictionary
        materials_from_inp(material_inp, array, indent, output_file)
    except Exception as e:
        _logger.exception('Material translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def materials_from_inp(
    material_inp, array=False, indent=None, output_file=None, dictionary=True
):
    """Translate all materials in an INP file to a honeybee JSON.

    The resulting JSON can be written into a user standards folder to add the
    materials to a users standards library.

    Args:
        material_inp: Full path to an INP file. Only the materials in this file
            will be extracted.
        array: Boolean to note whether a the output JSON should be an array of
            material objects or whether it should be a dictionary where each key
            is the identifier of the material and each value is the material
            object. The dictionary format is the one used by honeybee-standards and is
            recommended when writing INP materials into the user standards
            library. (Default: False).
        indent: Optional integer to specify the indentation in the output JSON file.
            Specifying an value here can produce more read-able JSONs. (Default: None).
        output_file: Optional JSON file to output the string of the translation.
            If None, it will be returned from this method. (Default: None).
    """
    # re-serialize the materials to Python
    window_constructions, _, materials = \
        extract_all_constructions_from_inp_file(material_inp)
    for w_con in window_constructions:
        materials.append(w_con.materials[0])
    # create the honeybee dictionaries
    out_dict = {}
    for mat in materials:
        out_dict[mat.identifier] = mat.to_dict()
    # convert the dictionary to an array if requested
    if array:
        out_dict = list(out_dict.values())
    # write out the JSON file
    return process_content_to_output(json.dumps(out_dict, indent=indent), output_file)


@translate.command('constructions-from-inp')
@click.argument('construction-inp', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option(
    '--full/--abridged', ' /-a', help='Flag to note whether the objects '
    'should be translated as an abridged specification instead of a '
    'specification that fully describes the object. This option should be '
    'used when the materials-from-inp command will be used to separately '
    'translate all of the materials from the INP.', default=True, show_default=True)
@click.option(
    '--dictionary/--array', ' /-a', help='Flag to note whether a the output JSON '
    'should be an array of objects or whether it should be a dictionary '
    'where each key is the identifier of the construction and each value is the '
    'construction object. The dictionary format is the one used by honeybee-standards '
    'and is recommended when writing INP constructions into the user standards library.',
    default=True, show_default=True)
@click.option(
    '--indent', '-i', help='Optional integer to specify the indentation in '
    'the output JSON file. Specifying an value here can produce more read-able'
    ' JSONs.', type=int, default=None, show_default=True)
@click.option(
    '--output-file', '-f', help='Optional JSON file to output the JSON string of '
    'the translation. By default this will be printed out to stdout',
    type=click.File('w'), default='-', show_default=True)
def constructions_from_inp_cli(construction_inp, full, dictionary, indent, output_file):
    """Translate all constructions in an INP file to a honeybee JSON.

    \b
    Args:
        construction_inp: Full path to a Construction INP file.
    """
    try:
        abridged = not full
        array = not dictionary
        constructions_from_inp(construction_inp, abridged, array, indent, output_file)
    except Exception as e:
        _logger.exception('Construction translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def constructions_from_inp(
    construction_inp, abridged=False, array=False, indent=None, output_file=None,
    full=True, dictionary=True
):
    """Translate all constructions in an INP file to a honeybee JSON.

    Args:
        construction_inp: Full path to a Construction INP file.
        array: Boolean to note whether a the output JSON should be an array of
            construction objects or whether it should be a dictionary where each key
            is the identifier of the construction and each value is the construction
            object. The dictionary format is the one used by honeybee-standards and is
            recommended when writing INP constructions into the user standards
            library. (Default: False).
        indent: Optional integer to specify the indentation in the output JSON file.
            Specifying an value here can produce more read-able JSONs. (Default: None).
        output_file: Optional JSON file path to output the JSON string of the
            translation. If None, the string will be returned from this function.
    """
    # re-serialize the constructions to Python
    window_constructions, opaque_constructions, _ = \
        extract_all_constructions_from_inp_file(construction_inp)
    # create the honeybee dictionaries
    out_dict = {}
    for con in opaque_constructions + window_constructions:
        try:
            out_dict[con.identifier] = con.to_dict(abridged=abridged)
        except TypeError:  # no abridged option
            out_dict[con.identifier] = con.to_dict()
    # convert the dictionary to an array if requested
    if array:
        out_dict = list(out_dict.values())
    # write out the JSON file
    return process_content_to_output(json.dumps(out_dict, indent=indent), output_file)
