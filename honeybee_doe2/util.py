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

        -   command: Text for the type of instruction that the DOE-2 object
                     executes.

        -   keywords: A list of text with the same length as the values that
                      denote the attributes of the DOE-2 object.

        -   values: A list of values with the same length as the keywords that
                    describe the values of the attributes for the object.
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

    # Handle default sections
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
        current_key = None
        value_lines = []
        in_braces = False

        for line in lines[1:]:
            stripped = line.strip()
            if not stripped:
                continue
            # Track whether we are inside a logic block
            # If/switch statements have to be inside {...} and contain 
            # multiple "=" lines
            if '{' in stripped:
                in_braces = True
            if '}' in stripped:
                value_lines.append(stripped)
                in_braces = False
                continue
            if '=' in stripped and not in_braces:
                # Save the previous key/value if any
                if current_key is not None:
                    keywords.append(current_key)
                    values.append('\n'.join(value_lines).strip())
                k, v = [s.strip() for s in stripped.split('=', 1)]
                current_key = k
                value_lines = [v] if v else []
            else:
                # Continuation line (inside logic block or multi-line value)
                value_lines.append(stripped)

        # Save last key/value
        if current_key is not None:
            keywords.append(current_key)
            values.append('\n'.join(value_lines).strip())
 
        command_type = ''  # Set to empty string for objects without TYPE attrs
        if "TYPE" in keywords:
            type_index = keywords.index("TYPE")
            command_type = values[type_index]

        return (command, command_type), "DEFAULTS", keywords, values

    doe2_fields = [e_str.strip() for e_str in inp_string.split('=')]
    u_name = doe2_fields.pop(0).replace('"', '')

    if not doe2_fields or not doe2_fields[0].strip():  # blank after '='
        return u_name, None, None, None

    split_field_1 = doe2_fields[0].split('\n')
    command = split_field_1[0].strip()

    if len(split_field_1) == 1:  # No keywords in command body

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
        global_parameters: A dict with parameter names as keys and
                           floats as values.
        input_expr: A string of an expression to be evaluated.
                    See an example below.

    Returns:
        Evaluated float result or None is not an inline math expression.

    .. code-block:: python

        '{0.66 * #PA("...")}' or '{0.66 * #PA("...") + #PA("...")}
    """
    # TODO: Add ability evaluate SWITCH and IF statements using Global Parms
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


def resolve_switch_value(switch_text, case_key):
    """Resolve a DOE-2 switch statement to the value for a given case key.

    Args:
        switch_text: The full switch block string
        example:
            {switch(#L("C-ACTIVITY-DESC"))
            case "npln": 215.198
            case "m5m2": 1075.99
            default: no_default
            endswitch}

        case_key: The case label to match
        example in above: 'npln'

    Returns:
        The resolved value as a string, or None if no matching case is found.
        For ``#SI(...)`` or ``#SIT(...)``  schedule references, the schedule
        name is extracted.
    """
    for line in switch_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith('case '):
            continue

        match = re.match(r'case\s+"([^"]+)":\s*(.*)', stripped)
        if match and match.group(1) == case_key:
            val = match.group(2).strip()
            # Extract schedule name from #SI("Name", "CMD", "KEY")
            si_match = re.match(r'#SI\(\s*\(?"([^"]+)"\)?,', val)
            if si_match:
                return '"{}"'.format(si_match.group(1))
            # DOE2.3 uses #SIT("Name", "CMD", "KEY", #L("TYPE"))
            sit_match = re.match(r'#SIT\(\s*\(?"([^"]+)"\)?,', val)
            if sit_match:
                return '"{}"'.format(sit_match.group(1))
            return val
    return None


def resolve_defaults(obj_attrs, defaults, keys):
    """Resolve attribute values for a DOE-2 command by merging its
    own attributes with SET-DEFAULT fallback values.

    The goal is for this to be generic and works for any command type
    (SPACE, ZONE, SYSTEM, etc.).

    Args:
        obj_attrs: The parsed attribute dict for the specific object instance
            (ie one SPACE or one ZONE from command_dict_from_inp)
        defaults: The merged DEFAULTS dict for this command type. For switch-
            based defaults, values will be resolved using the object's
            `C-ACTIVITY-DESC` attribute. Pass an empty dict if no defaults
            exist.
        keys: An iterable of INP keyword strings to resolve (e.g.
            `SPACE_KEYS` or `ZONE_KEYS`).

    Returns:
        A dict mapping each key to its resolved value (string or float).
        Keys that cannot be resolved from either source are ignored
    """
    resolved = {}
    # Strip '*' wrappers for SPACE and ZONE objects
    activity = str(obj_attrs.get('C-ACTIVITY-DESC', '')).replace(
        '*', '').strip()
    case_key = switch_statement_id(activity) if activity else ''

    for key in keys:
        # Check if keyword in commands dict
        val = obj_attrs.get(key)
        if val is not None:
            # Strip bracket wrappers
            if isinstance(val, str):
                val = val.strip()
                if val.startswith('(') and val.endswith(')'):
                    val = val[1:-1].strip()
                try:
                    val = float(val)
                except ValueError:
                    pass
            resolved[key] = val
            continue

        # Fall back to DEFAULTS if not in commands keyword dict
        default_val = defaults.get(key)
        if default_val is None:
            continue

        # If the default is a switch block, resolve it
        if isinstance(default_val, str) and 'switch' in default_val:
            switch_val = resolve_switch_value(default_val, case_key)
            if switch_val is not None:
                try:
                    switch_val = float(switch_val)
                except ValueError:
                    pass
                resolved[key] = switch_val
        else:
            resolved[key] = default_val

    return resolved


def find_user_lib_file():
    """Find the user's eQUEST library file (eQ_Lib.dat).

    This searches common eQuest installation paths in the users
    Documents folder, including OneDrive documents.

    TODO: Consider this an optional input for Model Editor?
    Returns:
        Path to eQ_Lib.dat if found, None otherwise.
    """
    filename = "eQ_Lib.dat"
    user_profile = os.environ.get('USERPROFILE', '')

    if not user_profile or not os.path.isdir(user_profile):
        return None

    doc_roots = []

    # Standard Documents folder
    standard_docs = os.path.join(user_profile, "Documents")
    if os.path.isdir(standard_docs):
        doc_roots.append(standard_docs)

    # OneDrive Documents folders (OneDrive - CompanyName pattern)
    for item in os.listdir(user_profile):
        item_path = os.path.join(user_profile, item)
        if os.path.isdir(item_path) and item.startswith("OneDrive"):
            onedrive_docs = os.path.join(item_path, "Documents")
            if os.path.isdir(onedrive_docs):
                doc_roots.append(onedrive_docs)

    # eQuest version folders, newest to oldest
    equest_folders = [
        "eQUEST 3-65-7175 Data",
        "eQUEST 3-65 Data",
        "eQUEST 3-64 Data",
        "eQUEST 3-63 Data",
    ]

    for root in doc_roots:
        for eq_folder in equest_folders:
            candidate = os.path.join(root, eq_folder, "DOE-2", filename)
            if os.path.isfile(candidate):
                return candidate

    return None


def _get_lib_content(lib_file_path, command_type):
    """Get library file blocks of a specific command type as a dict.

    Parses the library file into blocks keyed by entry name.

    Args:
        lib_file_path: Path to the library file.
        command_type: The DOE-2 command type to filter by ( ie 'SCHEDULE-PD',
            'WEEK-SCHEDULE-PD', 'DAY-SCHEDULE-PD').

    Returns:
        A dict mapping entry names to their raw block strings for the
        specified command type.
    """
    with open(lib_file_path, 'r') as lib_file:
        content = lib_file.read()

    blocks = {}
    # Split on $LIBRARY-ENTRY but keep the delimiter
    parts = re.split(r'(?=\$LIBRARY-ENTRY )', content)

    for part in parts:
        part = part.strip()
        if not part.startswith('$LIBRARY-ENTRY '):
            continue
        # Check if this block is the requested command type
        first_line = part.split('\n', 1)[0]
        if command_type not in first_line:
            continue

        header = first_line[len('$LIBRARY-ENTRY '):].strip()

        # Find position of command to extract name
        cmd_pos = header.find(command_type)
        if cmd_pos > 0:
            name = header[:cmd_pos].strip()
            blocks[name] = part

    return blocks


def parse_lib_string(lib_string, command_type):
    """Parse a library entry string from eQ_Lib.dat into a tuple of values.

    Library entries have a different format than standard INP strings:
    - First line: $LIBRARY-ENTRY <u_name>  <COMMAND>  <category>
    - Comment lines starting with $
    - Keyword-value pairs with indentation
    - Ends with ..

    Args:
        lib_string: A string for a single library entry block.
        command_type: The DOE-2 command type (ie 'SCHEDULE-PD',
            'WEEK-SCHEDULE-PD', 'DAY-SCHEDULE-PD').

    Returns:
        A tuple with three elements.

        -   u_name: Unique name of the library entry.

        -   keywords: A list of text with the same length as the values that
            denote the attributes of the object.

        -   values: A list of values with the same length as the keywords that
            describe the values of the attributes for the object.
    """
    lib_string = lib_string.strip()

    # Split off the terminator
    lib_strings = lib_string.rsplit('..', 1)
    assert len(lib_strings) >= 1, 'Input lib_string has no content.'

    lib_string = lib_strings[0]

    lines = lib_string.splitlines()
    if not lines:
        raise ValueError('Empty library string provided.')

    # Parse first line: $LIBRARY-ENTRY <u_name>  <COMMAND>
    first_line = lines[0]
    if not first_line.startswith('$LIBRARY-ENTRY '):
        raise ValueError(
            'Library string must start with '
            '$LIBRARY-ENTRY: {}'.format(first_line))

    # Remove the $LIBRARY-ENTRY prefix
    header = first_line[len('$LIBRARY-ENTRY '):].strip()

    # Find command position to extract name
    cmd_pos = header.find(command_type)
    if cmd_pos <= 0:
        raise ValueError(
            'Could not find {} in header: {}'.format(command_type, first_line))
    u_name = header[:cmd_pos].strip()

    # Collect non-comment lines for keyword parsing
    content_lines = []
    for line in lines[1:]:
        stripped = line.strip()
        # Skip comment lines (start with $)
        if stripped.startswith('$'):
            continue
        if stripped:
            content_lines.append(line)

    if not content_lines:
        return u_name, [], []

    # Join content and parse keyword-value pairs
    content = '\n'.join(content_lines)

    # Split by = to get keyword-value pairs
    doe2_fields = [e_str.strip() for e_str in content.split('=')]

    if not doe2_fields or not doe2_fields[0]:
        return u_name, [], []

    # First field is the first keyword
    keywords = [doe2_fields[0].strip()]
    values = []

    for field in doe2_fields[1:]:
        split_field = [f.strip() for f in field.split('\n')]
        if len(split_field) == 1:
            values.append(split_field[0])
        elif len(split_field) == 2 and not split_field[0].endswith(','):
            # Check if first line has unclosed parentheses
            paren_balance = split_field[0].count('(') - split_field[0].count(')')
            if paren_balance == 0:
                values.append(split_field[0])
                keywords.append(split_field[1])
            else:
                # Multi-line parenthesized value
                values.append(' '.join(split_field))
        else:
            v_lines, end_val = [], False
            paren_depth = 0
            for row in split_field:
                # Track parentheses depth to handle multi-line values
                paren_depth += row.count('(') - row.count(')')
                if row.endswith(',') or row.endswith('(') or paren_depth > 0:
                    v_lines.append(row)
                elif not end_val:
                    v_lines.append(row)
                    end_val = True
                else:
                    keywords.append(row)
            values.append(' '.join(v_lines))

    return u_name, keywords, values


def child_objects_from_parent(cmd_dict, parent_name, parent_command,
                              child_command):
    """Return all child_command objects between a parent's line and its next
    sibling.

    This requires the full dict of parsed INP blocks and one parent instance.

    Args:
        cmd_dict: Command dictionary containing all DOE2 objects.
        parent_name: Name of the parent from the object dict.
        parent_command: The command name of the parent.
        child_command: The command of the child objects to return.

    Returns:
        A dictionary with u_name strings for keys and dictionaries for values.
        This maps each child's u_name to its data dict whose __line__ is
        between the two parent lines.
    """
    # Sort the parents by __line__ just in case
    parents = cmd_dict.get(parent_command, {})
    sorted_parents = sorted(
        parents.items(),
        key=lambda item: item[1].get('__line__', float('inf'))
    )

    # Get the start line and end line
    start_line = None
    end_line = float('inf')
    for idx, (u_name, attrs) in enumerate(sorted_parents):
        if u_name == parent_name:
            start_line = attrs.get("__line__", -1)
            # find the next parents line, this will be the stopping point
            if idx + 1 < len(sorted_parents):
                end_line = sorted_parents[idx + 1][1].get('__line__', float('inf'))
            break

    # If we cant find the start then return empty dict
    if start_line is None:
        return {}

    # Find children in between the line
    children = cmd_dict.get(child_command, {})
    in_block = {
        c_name: c_data
        for c_name, c_data in children.items()
        if start_line < c_data.get('__line__', -1) < end_line
    }

    return in_block
