# coding=utf-8
"""Various utilities used throughout the package."""
from __future__ import division

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
            body_strs.append('   {}{}= ('.format(kwd, s, val))
            for v in val:
                body_strs.append('      {},'.format(v))
            body_strs.append('   )')
        else:
            body_strs.append('   {}{}= {}'.format(kwd, s, val))
    body_str = '\n'.join(body_strs)
    inp_str = '"{}" = {}\n{}\n   ..\n'.format(u_name, command, body_str)
    return inp_str


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
