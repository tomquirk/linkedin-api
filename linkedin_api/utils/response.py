from requests.models import Response
from typing import TypedDict, Optional, Any
from linkedin_api.utils.dict import denull_dict

from linkedin_api.utils.log import get_extra_log_content


class RawAPIResponse(TypedDict, total=False):
    status: int | None
    ok: bool | None
    data: Any | None


class APIResponse(TypedDict, total=False):
    message: str
    status: int | None
    ok: bool | None
    data: Any | None
    error: Optional[Any]
    notes: Optional[str]


def parse_api_response(response: Response | None = None,
                       status: int | str | None = None, data: Any | None = None,
                       max_parsed_data_text_length: int | None = 300) -> RawAPIResponse:
    result = {
        'status': None,
        'ok': None,
        'data': None,
    }

    if status is not None:
        result['status'] = int(status)
    elif response is not None:
        result['status'] = response.status_code

    if result['status'] is not None:
        result['ok'] = 200 <= result['status'] < 400

    if data is not None:
        result['data'] = data
    elif response is not None:
        try:
            # Try to parse the JSON response first
            new_data = response.json()
        except Exception:
            if max_parsed_data_text_length:
                # Failure to parse the JSON response will fall back to the orginal response text
                new_data = response.text[:max_parsed_data_text_length] + '... (truncated)' if len(
                    response.text) > max_parsed_data_text_length else response.text
            else:
                new_data = response.text

        result['data'] = new_data

    return result


def get_api_response_log(api_name,
                         response: Response | None = None,
                         status: int | str | None = None, data: Any | None = None,
                         user_id=None,
                         log_type: str | None = None,
                         max_parsed_data_text_length=300):

    api_response = parse_api_response(
        response, status, data, max_parsed_data_text_length)

    final_log_type = log_type
    if final_log_type is None:
        if api_response['ok'] is True:
            final_log_type = 'success'
        elif api_response['ok'] is False:
            final_log_type = 'failed'

    if final_log_type == 'normal':
        log = f"Retrieved {api_name} response"
    elif final_log_type == 'success':
        log = f"Successfully called {api_name}"
    elif final_log_type == 'failed':
        log = f"Failed to call {api_name}"
    else:
        log = f"Unknown action on {api_name}"

    if user_id:
        log += f" for ID {user_id}"

    del api_response['ok']
    log += get_extra_log_content(denull_dict(api_response))

    return log


def encode_api_response(message: str | None = None,
                        api_name: str | None = None,
                        response: Response | None = None,
                        status: int | str | None = None, data: Any | None = None,
                        error: str | None = None, notes: str | None = None,
                        user_id: str | None = None,
                        max_parsed_data_text_length: int | None = 300) -> APIResponse:
    raw_result = parse_api_response(response=response, status=status,
                                    data=data, max_parsed_data_text_length=max_parsed_data_text_length)

    result = {
        'message': message if message else get_api_response_log(
            api_name=api_name, user_id=user_id, log_type='success' if raw_result['ok'] else 'failed'),
        **raw_result,
    }

    if error:
        result['error'] = error

    if notes:
        result['notes'] = notes

    return result
