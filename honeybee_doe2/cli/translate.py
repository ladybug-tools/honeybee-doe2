"""honeybee-doe2 translation commands."""
import click
import sys
import os
import json
import logging

from ladybug.futil import write_to_file_by_name
from honeybee.model import Model

from honeybee_doe2.simulation import SimulationPar

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
    '--output-file', '-o', help='Optional INP file path to output the INP string '
    'of the translation. By default this will be printed out to stdout.',
    type=click.File('w'), default='-', show_default=True)
def model_to_inp_file(
    model_file, sim_par_json, hvac_mapping, include_interior_walls,
    include_interior_ceilings, output_file
):
    """Translate a Model (HBJSON) file to an INP file.

    \b
    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl)."""
    try:
        # load simulation parameters if specified
        sim_par = None
        if sim_par_json is not None:
            with open(sim_par_json) as json_file:
                data = json.load(json_file)
            sim_par = SimulationPar.from_dict(data)

        # re-serialize the Model to Python
        model = Model.from_file(model_file)
        x_int_w = not include_interior_walls
        x_int_c = not include_interior_ceilings

        # create the strings for the model
        inp_str = model.to.inp(model, sim_par, hvac_mapping, x_int_w, x_int_c)

        # write out the INP file
        output_file.write(inp_str)
    except Exception as e:
        _logger.exception(f'Model translation failed:\n{e}')
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('hbjson-to-inp')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
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
    '--verbose-properties/--switch-statements', ' /-ss', help='Flag to note whether '
    'program types should be written with switch statements so that they can easily '
    'be edited in eQuest or a verbose definition of loads should be written for '
    'each Room/Space.', default=True, show_default=True)
@click.option(
    '--name', '-n', help='Deprecated option to set the name of the output file.',
    default=None, show_default=True)
@click.option(
    '--folder', '-f', help='Deprecated option to set the path to target folder.',
    type=click.Path(file_okay=False, resolve_path=True, dir_okay=True), default=None)
@click.option(
    '--output-file', '-o', help='Optional INP file path to output the INP string '
    'of the translation. By default this will be printed out to stdout.',
    type=click.File('w'), default='-', show_default=True)
def hbjson_to_inp_file(
    model_file, hvac_mapping, include_interior_walls,
    include_interior_ceilings, verbose_properties, name, folder, output_file
):
    """Translate a Model (HBJSON) file to an INP file.

    \b
    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl)."""
    try:
        print('This method is deprecated and you should use model-to-inp instead.')
        model = Model.from_file(model_file)
        x_int_w = not include_interior_walls
        x_int_c = not include_interior_ceilings
        inp_str = model.to.inp(
            model, hvac_mapping=hvac_mapping, exclude_interior_walls=x_int_w,
            exclude_interior_ceilings=x_int_c)
        if folder is not None and name is not None:
            if not name.lower().endswith('.inp'):
                name = name + '.inp'
            write_to_file_by_name(folder, name, inp_str, True)
        else:
            output_file.write(inp_str)
    except Exception as e:
        _logger.exception(f'Model translation failed:\n{e}')
        sys.exit(1)
    else:
        sys.exit(0)
