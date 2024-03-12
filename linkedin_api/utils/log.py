def get_extra_log_content(content_dict: dict):
    if not content_dict:
        return ''

    log = ' with'

    # If more than 2 items, then we need to add comma
    add_comma = len(content_dict) > 2

    for index, key in enumerate(content_dict):
        value = content_dict[key]

        # Esacepe new line as it will be printed as a new line
        if isinstance(value, str) and '\n' in value:
            value = value.replace('\n', '\\n')

        # If it's the last item while it's not the first item, then add "and"
        if index != 0 and index == len(content_dict) - 1:
            log += f" and {key} {value}"
        else:
            log += f" {key} {value}," if add_comma else f" {key} {value}"

    return log
