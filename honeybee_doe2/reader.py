# coding=utf-8
"""Methods to read inp files to Honeybee."""
from __future__ import division
from collections import defaultdict

from .util import clean_inp_file_contents, doe2_object_blocks, parse_inp_string


def command_dict_from_inp(inp_file_contents):
    """Get a dictionary of INP commands and U-names from a INP file content string.

    Args:
        inp_file_contents: A text string of the complete contents of an INP file.

    Returns:
        A dictionary with all the DOE-2 attributes for each object
        converting keyword values to float when possible plus a "__line__"
        indicating its sequence in the file to be used to solve child/parent
        relationships {command: {u_name: {key: value, "__line__": line_number}}}
    """
    # clean the contents of the file and break it into blocks
    inp_file_contents = clean_inp_file_contents(inp_file_contents)
    blocks = doe2_object_blocks(inp_file_contents)
    global_parameters = {}
    non_parameter_blocks = []
    block_line_count = 1

    # Get globals first since they are formatted slightly differently
    for blk in blocks:
        u_name, cmd, keys, vals = parse_inp_string(blk)
        if cmd == "PARAMETER":
            key, val_raw = keys[0], vals[0]
            try:
                global_parameters[key] = float(val_raw)
            except ValueError:
                global_parameters[key] = val_raw
        else:
            non_parameter_blocks.append(blk)

    result = defaultdict(dict)

    for blk in non_parameter_blocks:
        u_name, cmd, keys, vals = parse_inp_string(blk)

        if keys is None or vals is None:
            continue  # ignore the block if it does not have any keywords

        attr_d = {}
        for k, v in zip(keys, vals):
            try:
                attr_d[k] = float(v)
            except ValueError:
                attr_d[k] = v
        attr_d["__line__"] = block_line_count
        block_line_count += 1
        result[cmd][u_name] = attr_d

    if global_parameters:
        result["PARAMETER"] = global_parameters

    return dict(result)
