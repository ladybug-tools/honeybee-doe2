from .util import parse_inp_file      

def structured_dict_from_inp(inp_file_path):
    """
    Read a DOE-2 INP file and return a Honeybee model.
    
    Args:
        inp_file_path: A path to the INP file to read.

    Returns:
        A structured dict with each DOE-2 objects and associated keyword/value pairs      
    """
    #  TODO: Loop over the inp_object_dict and create the Honeybee model object.
    return parse_inp_file(inp_file_path)

 


