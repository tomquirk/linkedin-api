from dateutil import parser
from datetime import datetime
import numbers
import pytz


def get_timezone_offset(timezone_str):
    # Create a timezone object based on the given timezone string
    timezone = pytz.timezone(timezone_str)

    # Get the current time in the given timezone
    now = datetime.now(timezone)

    # Calculate the offset in hours from UTC
    return int(now.utcoffset().total_seconds() / 3600)


def get_datetime(input_value: datetime | numbers.Number | str, tzinfo=pytz.timezone('Asia/Shanghai')) -> datetime:
    # If the input is already a datetime instance, return it directly
    if isinstance(input_value, datetime):
        return input_value
    elif isinstance(input_value, numbers.Number):
        return datetime.fromtimestamp(input_value, tz=tzinfo)

    # Try to parse a string or other date-time representations
    try:
        return parser.parse(str(input_value))
    except (ValueError, TypeError) as e:
        raise ValueError(
            f"Unable to parse the input value '{input_value}' into a datetime instance.") from e


def get_time_string(raw_time_object: datetime | numbers.Number | str, separator=None, tzinfo=pytz.timezone('Asia/Shanghai')):
    dt = get_datetime(raw_time_object)

    if separator is None:
        return dt.strftime('%Y-%m-%d %H:%M:%S.%f')
    else:
        return dt.strftime(f"%Y{separator}%m{separator}%d{separator}%H{separator}%M{separator}%S{separator}%f")
