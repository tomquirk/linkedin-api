from copy import deepcopy


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
