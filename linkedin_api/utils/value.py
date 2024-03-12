import ast
import urllib.parse


def boolean(value, default_value=False) -> bool:
    return True if value == 'True' or value == 'true' else default_value


def integer(value, default_value=None) -> int | None:
    return int(value) if value is not None and value != 'None' else default_value


def decode_unicode_string(unicode_string):
    """
    Convert a string containing Unicode escape sequences to its actual representation.

    Parameters:
    - unicode_string (str): A string with Unicode escape sequences.

    Returns:
    - str: A string with Unicode escape sequences converted to actual characters.
    """
    string = unicode_string.replace('\"', '\'')
    return str(ast.literal_eval(f'"{string}"'))


def decode_url_string(url_encoded_string):
    """
    Decode a URL-encoded string.

    Parameters:
    - url_encoded_string (str): A URL-encoded string.

    Returns:
    - str: A decoded string.
    """
    return urllib.parse.unquote(url_encoded_string)


def decode_garbled_string(garbled_string):
    # We need to encode it back to bytes assuming it was incorrectly interpreted as 'latin1'
    bytes_string = garbled_string.encode('latin1')

    # Now we decode it as 'utf-8'
    return bytes_string.decode('utf-8')
