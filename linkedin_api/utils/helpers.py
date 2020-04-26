import json


def get_id_from_urn(urn):
    """
    Return the ID of a given Linkedin URN.

    Example: urn:li:fs_miniProfile:<id>
    """
    return urn.split(":")[3]


def write_to_file(input_data, file_name):
    """
    Writes an input (whether or not JSON) to an output file
    """
    f = open(file_name, "w")
    if type(input_data) is dict:
        input_data = json.dumps(input_data)
    f.write(input_data)
    f.close()


def append_to_file(input_data, file_name):
    """
    Appends an input (whether or not JSON) to an output file
    """
    f = open(file_name, "a")
    if type(input_data) is dict:
        input_data = json.dumps(input_data)
    f.write(input_data)
    f.close()
