import json
from linkedin_api.utils.time import get_timezone_offset
from linkedin_api.utils.validate import is_nullable


def get_csrf_token_header(cookie_dict=None, j_session_id=None, enable_nullable_value_check=True):
    value = j_session_id if j_session_id else cookie_dict["JSESSIONID"].strip(
        '"')

    if enable_nullable_value_check and is_nullable(value):
        raise Exception(f"Invalid header value {value}")

    return {
        'csrf-token': value
    }


def get_x_li_track_header(timezone, display_width=1920, display_height=1080, display_density=1,
                          client_version="1.13.11901", os_name="web",
                          device_form_factor="DESKTOP", mp_name="voyager-web",
                          enable_nullable_value_check=True):
    track_content = {
        "clientVersion": client_version,
        "mpVersion": client_version,
        "osName": os_name,
        "timezoneOffset": get_timezone_offset(timezone),
        "timezone": timezone,
        "deviceFormFactor": device_form_factor,
        "mpName": mp_name,
        "displayDensity": display_density,
        "displayWidth": display_width,
        "displayHeight": display_height
    }

    if enable_nullable_value_check:
        for key, value in track_content.items():
            if is_nullable(value):
                raise Exception(
                    f"Invalid value {value} of key {key} in the JSON header")

    return {
        "x-li-track": json.dumps(track_content)
    }
