from datetime import datetime
import pytz


def get_timezone_offset(timezone_str):
    # Create a timezone object based on the given timezone string
    timezone = pytz.timezone(timezone_str)

    # Get the current time in the given timezone
    now = datetime.now(timezone)

    # Calculate the offset in hours from UTC
    return int(now.utcoffset().total_seconds() / 3600)
