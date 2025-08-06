# coding=utf-8
"""Various utilities used throughout the package."""
from __future__ import division

import os
import re


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

        -   u_name: Text for the unique name of the object. Will be None if
            the object is a Parameter. DOE-2 object defaults will return a
            tuple (command, command_type). For example, ZONE default u_name
            would be: ('ZONE', 'CONDITIONED')

        -   command: Text for the type of instruction that the DOE-2 object executes.

        -   keywords: A list of text with the same length as the values that denote
            the attributes of the DOE-2 object.

        -   values: A list of values with the same length as the keywords that describe
            the values of the attributes for the object.
    """
    inp_string = inp_string.strip()

    inp_strings = inp_string.rsplit('..', 1)  # r split incase '..' in u_name

    assert len(inp_strings) > 1, 'Input inp_string is not an INP object.'
    assert len(inp_strings) == 2, 'Received more than one object in inp_string.'

    inp_string = re.sub(r'\$.*\n', '\n', inp_strings[0])  # remove all comments

    if inp_string.startswith("PARAMETER"):
        lines = inp_string.splitlines()
        if len(lines) < 2:
            raise ValueError('Invalid parameter block: {}'.format(inp_string))
        param_line = lines[1].strip()

        if '=' in param_line:
            key, val = [s.strip().replace('"', '') for s in param_line.split('=', 1)]
            return None, "PARAMETER", [key], [val]
        else:
            raise ValueError(
                'Global parameter missing "=" assignment: {}'.format(inp_string))

    if inp_string.startswith("TITLE"):
        lines = inp_string.splitlines()[1:]  # Skip "TITLE"
        keywords = []
        values = []
        for line in lines:
            line = line.strip()
            if '=' in line:
                k, v = [s.strip().replace('"', '') for s in line.split('=', 1)]
                keywords.append(k)
                values.append(v)
        return None, "TITLE", keywords, values

    if inp_string.startswith("SET-DEFAULT FOR"):
        lines = inp_string.splitlines()

        # Get the command from the first line
        match = re.match(r"SET-DEFAULT FOR (\w+)", lines[0])
        if not match:
            raise ValueError(
                'Invalid SET-DEFAULT header: {}'.format(inp_string))
        command = match.group(1).strip()

        keywords = []
        values = []
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            if '=' in line:
                k, v = [s.strip().replace('"', '') for s in line.split('=', 1)]
                keywords.append(k)
                values.append(v)

        command_type = ''  # Set to empty string for objects without TYPE attrs
        if "TYPE" in keywords:
            type_index = keywords.index("TYPE")
            command_type = values[type_index]

        return (command, command_type), "DEFAULTS", keywords, values

    doe2_fields = [e_str.strip() for e_str in inp_string.split('=')]
    u_name = doe2_fields.pop(0).replace('"', '')

    if not doe2_fields or not doe2_fields[0].strip():     # blank after '='
        return u_name, None, None, None

    split_field_1 = doe2_fields[0].split('\n')
    command = split_field_1[0].strip()

    if len(split_field_1) == 1:  # Occurs when the object does not have any keywords
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


def calculate_value_with_global_parameter(global_parameters, input_expr):
    """Evaluate an INP Global Parameter expression with #PA("...").

    Note that this method will only return a float value if the expression is
    strictly an inline math expression.

    Args:
        global_parameters: A dict with parameter names as keys and floats as values.
        input_expr: A string of an expression to be evaluated. See an example below.

    Returns:
        Evaluated float result or None is not an inline math expression.

    .. code-block:: python

        '{0.66 * #PA("...")}' or '{0.66 * #PA("...") + #PA("...")}
    """
    # TODO: Add the ability to evaluate SWITCH and IF statements using GlobaL Parameters
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
                expr = expr.replace('#PA("{}")'.format(param_name), param_val)
        return eval(expr, {'__builtins__': None}, {})
    except Exception:
        return None


def doe2_object_blocks(inp_file_contents):
    """Get the object blocks of a DOE-2 INP file.

    Args:
        inp_file_contents: A string of the INP file to parse.

    Returns:
        A list of strings, where each string is a complete block of the INP file.
    """
    blocks, buffer = [], []
    ignore_blocks = ['INPUT', 'END', 'COMPUTE', 'STOP']

    for line in inp_file_contents.splitlines():
        buffer.append(line)
        if line.strip().endswith('..'):
            if not any(buffer[0].strip().startswith(b) for b in ignore_blocks):
                blocks.append('\n'.join(buffer))
                buffer = []
            else:
                buffer = []
                continue

    if buffer:
        blocks.append('\n'.join(buffer))

    return blocks


def clean_inp_file_contents(inp_file_contents):
    """Clean an INP file's text.

    This includes removing comment lines and resolving inline #PA() parameter
    expressions.

    Args:
        inp_file_contents: Complete text of an INP file.

    Returns:
        The cleaned text, ready for further parsing.
    """
    lines = inp_file_contents.splitlines(keepends=True)  # keep original new-lines
    global_parameters = {}
    file_lines = []

    i = 0
    while i < len(lines):
        full_line = lines[i]
        stripped = full_line.strip()

        if stripped == "PARAMETER":
            param_block = [full_line]
            i += 1
            while i < len(lines):
                param_block.append(lines[i])
                if lines[i].strip().endswith(".."):
                    break
                i += 1
            full_param = "".join(param_block)
            _, _, keys, vals = parse_inp_string(full_param)
            global_parameters[keys[0]] = vals[0]
            file_lines.extend(param_block)
            i += 1
            continue

        if "#PA" in full_line:
            def _repl(match):
                expr = match.group(1)
                val = calculate_value_with_global_parameter(global_parameters, expr)
                return str(val) if val is not None else match.group(0)
            full_line = re.sub(r"\{([^}]*#PA\(\".*?\"\)[^}]*)\}", _repl, full_line)

        if not stripped.startswith("$"):
            file_lines.append(full_line)

        i += 1

    return "".join(file_lines)


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


def inp_path_from_folder(folder_path=None, filename=None):
    """Get the path to an INP file from a specified folder or the current directory.

    Args:
        folder_path: Path to the folder containing the INP file. If None, the
            current directory will be used.
        filename: Name of the INP file. If None, the first file found in the folder
            with an .inp extension will be returned

    Returns:
        Path to the INP file.

    Raises:
        FileNotFoundError: If no INP file is found.
    """
    # process the folder path input
    if folder_path is None:
        folder_path = os.getcwd()
    else:
        assert os.path.isdir(folder_path), \
            'No directory was found at: {}'.format(folder_path)

    # process the filename
    if filename is None:  # Look for any .inp file in the folder
        found_files = []
        for f_name in os.listdir(folder_path):
            if f_name.lower().endswith('*.inp'):
                found_files.append(os.path.join(folder_path, f_name))
        if len(found_files) == 0:
            raise FileNotFoundError('No .inp files found in {}'.format(folder_path))
        elif len(found_files) > 1:
            # If multiple INP files, use the first one (you might want to be more specific)
            print('Multiple .inp files found, using: {}'.format(found_files[0]))
        return found_files[0]
    else:  # Use the specified filename
        inp_path = os.path.join(folder_path, filename)
        assert os.path.isfile(inp_path), \
            'No INP file was found at: {}'.format(inp_path)
        return inp_path
