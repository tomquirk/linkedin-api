from copy import deepcopy
import numbers
import re
from .validate import is_nullable
from .value import decode_garbled_string, decode_unicode_string, decode_url_string


def get_value(dictionary: dict, key: str, default=None, filter_out_null=True, raise_error=False, key_separator='|', logging_cb=None):
    if not dictionary:
        return default

    try:
        current_value = deepcopy(dictionary)
        for sub_key in key.split(key_separator):
            current_value = current_value[sub_key]

        if isinstance(current_value, str):
            return current_value if not filter_out_null else re.sub(r'[\x00-\x1F]', '', current_value)

        return current_value
    except KeyError as e:
        if logging_cb:
            logging_cb(
                f"Get value from {dictionary} with key {key} failed with the following error")
            logging_cb(e)

        if raise_error:
            raise e

        return default


def rename_key(dict, old_key, new_key):
    if old_key in dict:
        dict[new_key] = dict.pop(old_key)
    return dict


def denull_dict(dict):
    new_dict = {}
    for key, value in dict.items():
        if not is_nullable(value):
            new_dict[key] = value

    return new_dict


def format_profile_dict(dict):
    new_dict = {}
    for key, value in dict.items():
        new_value = value

        if value is None:
            new_dict[key] = new_value
            continue

        if isinstance(new_value, numbers.Number):
            new_dict[key] = new_value
            continue

        # Matches 4 digits for the year, a comma, and 1 or 2 digits for the month
        if bool(re.match(r"^\d{4},\d{1,2}$", value)):
            new_value = value.replace(',', '.')

        try:
            new_value = decode_unicode_string(new_value)
        except Exception as e:
            new_value = new_value

        try:
            new_value = decode_url_string(new_value)
        except Exception as e:
            new_value = new_value

        try:
            new_value = decode_garbled_string(new_value)
        except Exception as e:
            new_value = new_value

        new_value = re.sub(r'[\x00-\x1F]', '', new_value)

        new_dict[key] = new_value

    return new_dict
