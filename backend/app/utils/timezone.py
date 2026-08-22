from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

def is_valid_timezone(tz_name: str) -> bool:
    """
    Checks if a timezone string is a valid IANA timezone name.
    """
    try:
        ZoneInfo(tz_name)
        return True
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        return False

def local_to_utc(date_str: str, time_str: str, tz_name: str) -> datetime:
    """
    Interprets local date and time strings under the specified IANA timezone
    and converts the resulting local time into a timezone-aware UTC datetime.
    """
    tz = ZoneInfo(tz_name)
    naive_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_dt = naive_dt.replace(tzinfo=tz)
    return local_dt.astimezone(ZoneInfo("UTC"))
