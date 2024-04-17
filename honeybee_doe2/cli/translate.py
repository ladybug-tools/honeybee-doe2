"""honeybee-doe2 Translation Commands"""
import click
import sys
import pathlib
import logging

from ..writer import honeybee_model_to_inp
from honeybee.model import Model

_logger = logging.getLogger(__name__)


@click.group(help='Commands for translating Honeybee_Model.hbjson to DOE2.2 *.inp files.')
def translate():
    pass


@translate.command('hbjson-to-inp')
@click.argument('hb-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True)
)
@click.option(
    '--hvac-mapping', '-hm', help='HVAC mapping method. Options are room, story, model '
    'or assigned-hvac.',
    default='story', show_default=True, type=click.Choice(
    ['room', 'story', 'model', 'assigned-hvac'], case_sensitive=False))

@click.option(
    '--exclude-interior-walls', '-eiw', help='Use this flag to exclude interior walls from export',
    default=False, show_default=True, is_flag=True
)

@click.option(
    '--exclude-interior-ceilings', '-eic', help='Use this flag to exclude interior ceilings from export',
    default=False, show_default=True, is_flag=True
)

@click.option(
    '--switch-statements', '-swi', help='Use this flag to export *.inp file with switch statements',
    default=False, show_default=True, is_flag=True
)

@click.option('--name', '-n', help='Name of the output file.', default='model',
              show_default=True
              )

@click.option('--folder', '-f', help='Path to target folder.', type=click.Path(
    exists=False, file_okay=False, resolve_path=True, dir_okay=True),
    default='.', show_default=True
)
def hb_model_to_inp_file(hb_json, hvac_mapping, exclude_interior_walls, exclude_interior_ceilings, switch_statements, name, folder):
    """Translate a HBJSON into a DOE2.2 *.inp file."""
    try:
        hvac_mapping
        hb_model = Model.from_file(hb_json)
        folder = pathlib.Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        honeybee_model_to_inp(hb_model, hvac_mapping, exclude_interior_walls, exclude_interior_ceilings,switch_statements, folder, name)
    except Exception as e:
        _logger.exception(f'Model translation failed:\n{e}')
        sys.exit(1)
    else:
        sys.exit(0)
