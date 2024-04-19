# coding=utf-8
"""Methods to write to inp."""


def shade_mesh_to_inp(shade_mesh):
    """Generate an INP string representation of a ShadeMesh.

    Args:
        shade_mesh: A honeybee ShadeMesh for which an INP representation
            will be returned.
        
    Returns:
        A tuple with two elements.

        -   shade_polygons: A list of text strings for the INP polygons needed
            to represent the ShadeMesh.

        -   shade_defs: A list of text strings for the INP definitions needed
            to represent the ShadeMesh.
    """
    # TODO: write the real code
    return None, None


def shade_to_inp(shade):
    """Generate an INP string representation of a Shade.

    Args:
        shade: A honeybee Shade for which an INP representation will be returned.

    Returns:
        A tuple with two elements.

        -   shade_polygon: Text string for the INP polygon for the Shade.

        -   shade_def: Text string for the INP definition of the Shade.
    """
    # TODO: write the real code
    return None, None


def door_to_inp(door):
    """Generate an INP string representation of a Door.

    Doors assigned to a parent Face will use the parent Face plane in order to
    determine their XY coordinates. Otherwise, the Door's own plane will be used.

    Note that the resulting string does not include full construction definitions.
    Also note that shades assigned to the Door are not included in the resulting
    string. To write these objects into a final string, you must loop through the
    Door.shades, and call the to.inp method on each one.

    Args:
        door: A honeybee Door for which an INP representation will be returned.

    Returns:
        Text string for the INP definition of the Door.
    """
    # TODO: write the real code
    return None


def aperture_to_inp(aperture):
    """Generate an INP string representation of a Aperture.

    Apertures assigned to a parent Face will use the parent Face plane in order to
    determine their XY coordinates. Otherwise, the Aperture's own plane will be used.

    Note that the resulting string does not include full construction definitions.
    Also note that shades assigned to the Aperture are not included in the resulting
    string. To write these objects into a final string, you must loop through the
    Aperture.shades, and call the to.inp method on each one.

    Args:
        aperture: A honeybee Aperture for which an INP representation will be returned.

    Returns:
        Text string for the INP definition of the Aperture.
    """
    # TODO: write the real code
    return None


def face_to_inp(face):
    """Generate an INP string representation of a Face.

    Note that the resulting string does not include full construction definitions.

    Also note that this does not include any of the shades assigned to the Face
    in the resulting string. Nor does it include the strings for the
    apertures or doors. To write these objects into a final string, you must
    loop through the Face.apertures, and Face.doors and call the to.inp method
    on each one.

    Args:
        face: A honeybee Face for which an INP representation will be returned.
    
    Returns:
        A tuple with two elements.

        -   face_polygon: Text string for the INP polygon for the Face.

        -   face_def: Text string for the INP definition of the Face.
    """
    # TODO: write the real code
    return None, None


def room_to_inp(room):
    """Generate an INP string representation of a Room.

    The resulting string will include all internal gain definitions for the Room
    (people, lights, equipment), infiltration definitions, ventilation requirements,
    and thermostat objects. However, complete schedule definitions assigned to
    these objects are excluded.

    Also note that this method does not write any of of the Room's constituent
    Faces Shades, or windows into the resulting string. To represent the full
    Room geometry, you must loop through the Room.faces and call the to.inp
    method on each one.

    Args:
        room: A honeybee Room for which an INP representation will be returned.
    
    Returns:
        A tuple with two elements.

        -   room_polygon: Text string for the INP polygon for the Room.

        -   room_def: Text string for the INP SPACE definition of the Room.
    """
    # TODO: write the real code
    return None, None


def model_to_inp(
    model, hvac_mapping='Story', exclude_interior_walls=False,
    exclude_interior_ceilings=False
):
    """Generate an INP string representation of a Model.

    The resulting string will include all geometry (Rooms, Faces, Apertures,
    Doors, Shades), all fully-detailed constructions + materials, all fully-detailed
    schedules, and the room properties.

    Essentially, the string includes everything needed to simulate the model
    except the simulation parameters. So joining this string with the output of
    SimulationParameter.to_inp() should create a simulate-able INP.

    Args:
        model: A honeybee Model for which an INP representation will be returned.
        hvac_mapping: Text to indicate how HVAC systems should be assigned to the
            exported model. Story will assign one HVAC system for each distinct
            level polygon, Model will use only one HVAC system for the whole model
            and AssignedHVAC will follow how the HVAC systems have been assigned
            to the Rooms.properties.energy.hvac. Choose from the options
            below. (Default: Story).

            * Room
            * Story
            * Model
            * AssignedHVAC

        exclude_interior_walls: Boolean to note whether interior wall Faces
            should be excluded from the resulting string. (Default: False).
        exclude_interior_ceilings: Boolean to note whether interior ceiling
            Faces should be excluded from the resulting string. (Default: False).
    
    Usage:

    .. code-block:: python

        import os
        from ladybug.futil import write_to_file
        from honeybee.model import Model
        from honeybee.room import Room
        from honeybee.config import folders
        from honeybee_doe2.simulation import SimulationParameter

        # Get input Model
        room = Room.from_box('Tiny House Zone', 5, 10, 3)
        room.properties.energy.program_type = office_program
        room.properties.energy.add_default_ideal_air()
        model = Model('Tiny House', [room])

        # Get the input SimulationParameter
        sim_par = SimulationParameter()

        # create the INP string for simulation parameters and model
        inp_str = '\n\n'.join((sim_par.to_inp(), model.to.inp(model)))

        # write the final string into an INP
        inp = os.path.join(folders.default_simulation_folder, 'test_file', 'in.inp')
        write_to_file(inp, inp_str, True)
    """
    # duplicate model to avoid mutating it as we edit it for energy simulation
    original_model = model
    model = model.duplicate()

    # scale the model if the units are not feet
    if model.units != 'Feet':
        model.convert_to_units('Feet')
    # remove degenerate geometry within native DOE-2 tolerance of 0.1 feet
    try:
        model.remove_degenerate_geometry(0.1)
    except ValueError:
        error = 'Failed to remove degenerate Rooms.\nYour Model units system is: {}. ' \
            'Is this correct?'.format(original_model.units)
        raise ValueError(error)

    # TODO: split all of the Rooms with holes so that they can be translated
    # convert all of the Aperture geometries to rectangles so they can be translated
    model.rectangularize_apertures(
        subdivision_distance=0.5, max_separation=0.0,
        merge_all=True, resolve_adjacency=True
    )

    # TODO: reassign stories to the model such that each has only one polygon

    # TODO: overwrite all identifiers to obey the eQuest 32 character length