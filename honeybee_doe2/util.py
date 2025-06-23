# coding=utf-8
"""Various utilities used throughout the package."""
from __future__ import division

import re
import os
from collections import defaultdict
from pathlib import Path

def generate_inp_string(u_name, command, keywords, values):
    """Get an INP string representation of a DOE-2 object.

    This method is written in a generic way so that it can describe practically
    any element of the INP Building Description Language (BDL).

    Args:
        u_name: Text for the unique, user-specified name of the object being created.
            This must be 32 characters or less and not contain special or non-ASCII
            characters. The clean_doe2_string method may be used to convert
            strings to a format that is acceptable here. For example, a U-Name
            of a space might be "Floor2W ClosedOffice5".
        command: Text indicating the type of instruction that the DOE-2 object
            executes. Commands are typically in capital letters and examples
            include POLYGON, FLOOR, SPACE, EXTERIOR-WALL, WINDOW, CONSTRUCTION, etc.
        keywords: A list of text with the same length as the values that denote
            the attributes of the DOE-2 object.
        values: A list of values with the same length as the keywords that describe
            the values of the attributes for the object.

    Returns:
        inp_str -- A DOE-2 INP string representing a single object.
    """
    space_count = tuple((25 - len(str(n))) for n in keywords)
    spc = tuple(s_c * ' ' if s_c > 0 else ' ' for s_c in space_count)
    body_str = '\n'.join('   {}{}= {}'.format(kwd, s, val)
                         for kwd, s, val in zip(keywords, spc, values))
    inp_str = '"{}" = {}\n{}\n   ..\n'.format(u_name, command, body_str)
    return inp_str


def generate_inp_string_list_format(u_name, command, keywords, values):
    """Get an INP string of a DOE-2 object with nicer formatting for list values.

    This method will process any values that are a list or tuple and format them
    such that they are indented and more readable. This method is written in a
    generic way so that it can describe practically any element of the INP Building
    Description Language (BDL).

    Args:
        u_name: Text for the unique, user-specified name of the object being created.
            This must be 32 characters or less and not contain special or non-ASCII
            characters. The clean_doe2_string method may be used to convert
            strings to a format that is acceptable here. For example, a U-Name
            of a space might be "Floor2W ClosedOffice5".
        command: Text indicating the type of instruction that the DOE-2 object
            executes. Commands are typically in capital letters and examples
            include POLYGON, FLOOR, SPACE, EXTERIOR-WALL, WINDOW, CONSTRUCTION, etc.
        keywords: A list of text with the same length as the values that denote
            the attributes of the DOE-2 object.
        values: A list of values with the same length as the keywords that describe
            the values of the attributes for the object. The items in this list
            can be list themselves, in which case they will be translated with
            nice indented formatting.

    Returns:
        inp_str -- A DOE-2 INP string representing a single object.
    """
    space_count = tuple((25 - len(str(n))) for n in keywords)
    spc = tuple(s_c * ' ' if s_c > 0 else ' ' for s_c in space_count)
    body_strs = []
    for kwd, s, val in zip(keywords, spc, values):
        if isinstance(val, (list, tuple)):
            body_strs.append('   {}{}= ('.format(kwd, s))
            for v in val:
                body_strs.append('      {},'.format(v))
            body_strs.append('   )')
        else:
            body_strs.append('   {}{}= {}'.format(kwd, s, val))
    body_str = '\n'.join(body_strs)
    inp_str = '"{}" = {}\n{}\n   ..\n'.format(u_name, command, body_str)
    return inp_str


def clean_inp_file_contents(inp_file):
    """Get the contents of an INP file without comment lines and global parameter
        lines solved if they are inline math expressions.

    Args:
        inp_file: A path to the INP file containing objects to be parsed.

    Returns:
        A single string for the clean INP file contents.

    """
    assert os.path.isfile(inp_file), 'Cannot find an INP file at: {}'.format(inp_file)
    
    global_parameters = {}
    file_lines = []
    with open(inp_file, 'r') as doe_file:
        lines = doe_file.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line == "PARAMETER":
            param_block = [lines[i]]
            i += 1
            while i < len(lines):
                param_block.append(lines[i])
                if lines[i].strip().endswith(".."):
                    break
                i += 1
            full_param = ''.join(param_block)

            _, _, keys, vals = parse_inp_string(full_param)
            # Save the parameter to solve the lines later
            global_parameters[keys[0]] = vals[0]
            file_lines.extend(param_block)
            i += 1
            continue
 
        # Try and replace/remove the global parameters expressions
        if '#PA' in line:
      
            matches = re.finditer(r'{([^}]*#PA\(".*?"\)[^}]*)}', line)
            for m in matches:
                expr = m.group(1)
                replacement = calculate_value_with_global_parameter(global_parameters, expr)
                if replacement is not None:
                    line = line.replace(expr, str(replacement))
        # Skip comment lines
        if not line.startswith('$'):
            file_lines.append(lines[i])

        i += 1

    return ''.join(file_lines)

def calculate_value_with_global_parameter(global_parameters, input_expr):
    """
    Evaluate a Global Parameter expression with #PA("...") if it is strickly an 
    inline math expression.

    Args:
        global_parameters: dict of parameter_name → numeric_value
        input_expr: a string like => '{0.66 * #PA("...")}' or '{0.66 * #PA("...") + #PA("...")}

    Returns:
        Evaluated float result or None
    
    TODO: Add the ability to evaluate SWITCH and IF statements using GlobaL Parmeters
    """
    try:
        # Remove curly braces
        expr = input_expr.strip()
        if expr.startswith('{') and expr.endswith('}'):
            expr = expr[1:-1].strip()

        matches = re.findall(r'#PA\(\s*"([^"]+)"\s*\)', expr)
        
        # replace each match in case of multiple #PA expressions
        for param_name in matches:
            if param_name in global_parameters:
                param_val = str(global_parameters[param_name])
                expr = expr.replace(f'#PA("{param_name}")', param_val) 
        return eval(expr, {"__builtins__": None}, {})
    
    except Exception:
        return None 

def parse_inp_string(inp_string):
    """Parse an INP string of a single DOE-2 object into a list of values.

    Note that this method is only equipped to parse DOE-2 test strings
    that originate from eQuest or from this package. It has not yet
    been generalized to parse all formats of text formats that can
    appear in a DOE-2 file.

    Args:
        inp_string: An INP string for a single DOE-2 object.

    Returns:
        A tuple with four elements.

        -   u_name: Text for the unique name of the object. None if the object is a Parameter.

        -   command: Text for the type of instruction that the DOE-2 object executes.

        -   keywords: A list of text with the same length as the values that denote
            the attributes of the DOE-2 object.

        -   values: A list of values with the same length as the keywords that describe
            the values of the attributes for the object.
    """
    inp_string = inp_string.strip()
    inp_strings = inp_string.split('..')
    assert len(inp_strings) == 2, 'Received more than one object in inp_string.'
    inp_string = re.sub(r'\$.*\n', '\n', inp_strings[0])  # remove all comments
    
    if inp_string.startswith("PARAMETER"):
        lines = inp_string.splitlines()
        if len(lines) < 2:
            raise ValueError(f"Invalid parameter block: {inp_string!r}")
        param_line = lines[1].strip()
        if '=' in param_line:
            key, val = [s.strip().replace('"', '') for s in param_line.split('=', 1)]
            return None, "PARAMETER", [key], [val]
        else:
            raise ValueError(f"Global parameter missing '=' assignment: {inp_string!r}")

    doe2_fields = [e_str.strip() for e_str in inp_string.split('=')]
    u_name = doe2_fields.pop(0).replace('"', '')
    split_field_1 = doe2_fields[0].split('\n')
    command = split_field_1[0].strip()
    
    if len(split_field_1) == 1: # Occurs when the object does not have any keywords
        return u_name, command, None, None

    keywords = [split_field_1[1].strip()]

    values = []
    for field in doe2_fields[1:]:
        split_field = [f.strip() for f in field.split('\n')]
        if len(split_field) == 1:
            values.append(split_field[0])
        elif len(split_field) == 2 and not split_field[0].endswith(','):
            values.append(split_field[0])
            keywords.append(split_field[1])
        else:
            v_lines, end_val = [], False
            for row in split_field:
                if row.endswith(',') or row.endswith('('):
                    v_lines.append(row)
                elif not end_val:
                    v_lines.append(row)
                    end_val = True
                else:
                    keywords.append(row)
            values.append(' '.join(v_lines))
    return u_name, command, keywords, values




def get_doe2_object_blocks(inp_file):
    """
    Get the object blocks of a DOE-2 INP file.

    Args:
        inp_file: A string of the INP file to parse.

    Returns:
        A list of strings, each string is a complete block of the INP file.
    """
    blocks, buffer = [], []
    
    ignore_blocks = ['INPUT', 'TITLE' , 'END', 'COMPUTE', 'STOP']

    for line in inp_file.splitlines():
        buffer.append(line)
        if line.strip().endswith(".."): 
            if not any(buffer[0].strip().startswith(b) for b in ignore_blocks):
                blocks.append('\n'.join(buffer))
                buffer = []
            else:
                buffer = []
                continue

    if buffer:
        blocks.append('\n'.join(buffer))

    return blocks


def parse_inp_file(inp_file_path):
    """
    Parse a DOE‑2 INP file into a dict

    Args:
        inp_file_path: A path to the INP file to parse.

    Returns:
        A dictionary {command: {u_name: {key: value}}}
    """

    inp_file = clean_inp_file_contents(inp_file_path)
    blocks = get_doe2_object_blocks(inp_file)
    global_parameters = {}
    non_parameter_blocks = []

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
            continue # ignore the block if it does not have any keywords

        attr_d = {}
        for k, v in zip(keys, vals):
            try:
                attr_d[k] = float(v)
            except ValueError:
                attr_d[k] = v
        result[cmd][u_name] = attr_d

    if global_parameters:
        result["PARAMETER"] = global_parameters

    return dict(result)



def header_comment_minor(header_text):
    """Create a header given header_text, which can help organize the INP file contents.
    """
    return \
        '$ ---------------------------------------------------------\n' \
        '$              {}\n' \
        '$ ---------------------------------------------------------\n'\
        '\n'.format(header_text)


def header_comment_major(header_text):
    """Create a header given header_text, which can help organize the INP file contents.
    """
    return \
        '$ *********************************************************\n' \
        '$ **                                                     **\n' \
        '$                   {}\n' \
        '$ **                                                     **\n' \
        '$ *********************************************************\n'\
        '\n'.format(header_text)


def switch_statement_id(value):
    """Convert a string into a 4-character ID that can be used for switch statements.

    This is needed to deal with the major limitations that DOE-2 places on
    switch statement IDs, where every ID must be 4 characters
    """
    # first remove dangerous characters
    val = re.sub(r'[^.A-Za-z0-9:]', '', value)  # remove all unusable characters
    val = val.replace(' ', '').replace('_', '')  # remove spaces and underscores

    # the user has formatted their program id specifically for switch statements
    if len(val) <= 4:
        return val

    # remove lower-case vowels for readability
    val = re.sub(r'[aeiouy_\-]', '', val)
    if '::' in val:  # program id originating from openstudio-standards
        val = val.split('::')[-1]
        if len(val) >= 4:
            return val[:4]

    # some special user-generated program id
    val = val.replace(':', '')
    if len(val) >= 4:
        return val[-4:]
    return val

def get_inp_path_from_folder(folder_path=None, filename=None):
    """
    Get the path to an INP file from a specified folder or the current directory.
    
    Args:
        folder_path: Path to the folder containing the INP file. If None, uses current directory.
        filename: Name of the INP file. If None, looks for any .inp file in the folder.
        
    Returns:
        Path to the INP file.
        
    Raises:
        FileNotFoundError: If no INP file is found.
    """
    if folder_path is None:
        folder_path = Path.cwd()
    else:
        folder_path = Path(folder_path)
    
    if filename is None:
        # Look for any .inp file in the folder
        inp_files = list(folder_path.glob("*.inp"))
        if not inp_files:
            raise FileNotFoundError(f"No .inp files found in {folder_path}")
        if len(inp_files) > 1:
            # If multiple INP files, use the first one (you might want to be more specific)
            print(f"Multiple .inp files found, using: {inp_files[0]}")
        return inp_files[0]
    else:
        # Use the specified filename
        inp_path = folder_path / filename
        if not inp_path.exists():
            raise FileNotFoundError(f"INP file not found: {inp_path}")
        return inp_path


def load_inp_from_same_folder(filename=None):
    """
    Load an INP file from the same folder as the current script.
    
    Args:
        filename: Name of the INP file. If None, looks for any .inp file.
        
    Returns:
        Path to the INP file.
    """
    # Get the directory where the current script is located
    script_dir = Path(__file__).parent
    return get_inp_path_from_folder(script_dir, filename)
