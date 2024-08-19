import calendar
from datetime import datetime, timedelta
import locale
import re
import time

from dateutil.parser import parse as dateutil_parse
from dateutil.tz import tzlocal
from parsedatetime.parsedatetime import Calendar
import contextlib

locale.setlocale(locale.LC_ALL, "")
fuzzy_date_parse = Calendar().parse
fuzzy_datetime_parse = Calendar().parseDT


REMINDER_REGEX = r"^(\d+)([wdhm]?)(?:\s+(popup|email|sms))?$"

DURATION_REGEX = re.compile(
    r"^((?P<days>[\.\d]+?)(?:d|day|days))?[ :]*"
    r"((?P<hours>[\.\d]+?)(?:h|hour|hours))?[ :]*"
    r"((?P<minutes>[\.\d]+?)(?:m|min|mins|minute|minutes))?[ :]*"
    r"((?P<seconds>[\.\d]+?)(?:s|sec|secs|second|seconds))?$"
)


def parse_reminder(rem):
    match = re.match(REMINDER_REGEX, rem)
    if not match:
        # Allow argparse to generate a message when parsing options
        return None
    n = int(match[1])
    t = match[2]
    m = match[3]
    if t == "w":
        n = n * 7 * 24 * 60
    elif t == "d":
        n = n * 24 * 60
    elif t == "h":
        n *= 60

    if not m:
        m = "popup"

    return n, m


def set_locale(new_locale):
    try:
        locale.setlocale(locale.LC_ALL, new_locale)
    except locale.Error as exc:
        raise ValueError(
            f"Error: {exc!s}" + "!\n Check supported locales of your system.\n"
        ) from exc


def get_times_from_duration(when, duration=0, allday=False):
    try:
        start = get_time_from_str(when)
    except Exception as e:
        msg = f"Date and time is invalid: {when}\n"
        raise ValueError(msg) from e

    if allday:
        try:
            stop = start + timedelta(days=float(duration))
        except Exception as exc:
            msg = f"Duration time (days) is invalid: {duration}\n"
            raise ValueError(msg) from exc

        start = start.date().isoformat()
        stop = stop.date().isoformat()

    else:
        try:
            stop = start + get_timedelta_from_str(duration)
        except Exception as exc:
            msg = f"Duration time is invalid: {duration}\n"
            raise ValueError(msg) from exc

        start = start.isoformat()
        stop = stop.isoformat()

    return start, stop


def get_time_from_str(when):
    """Convert a string to a time: first uses the dateutil parser, falls back
    on fuzzy matching with parsedatetime.
    """
    zero_oclock_today = datetime.now(tzlocal()).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    try:
        event_time = dateutil_parse(when, default=zero_oclock_today)
    except ValueError as e:
        struct, result = fuzzy_date_parse(when)
        if not result:
            msg = f"Date and time is invalid: {when}"
            raise ValueError(msg) from e
        event_time = datetime.fromtimestamp(time.mktime(struct), tzlocal())

    return event_time


def get_timedelta_from_str(delta):
    """Parse a time string a timedelta object.
    Formats:
      - number -> duration in minutes
      - "1:10" -> hour and minutes
      - "1d 1h 1m" -> days, hours, minutes
    Based on https://stackoverflow.com/a/51916936/12880.
    """
    parsed_delta = None
    with contextlib.suppress(ValueError):
        parsed_delta = timedelta(minutes=float(delta))
    if parsed_delta is None:
        parts = DURATION_REGEX.match(delta)
        if parts is not None:
            with contextlib.suppress(ValueError):
                time_params = {
                    name: float(param)
                    for name, param in parts.groupdict().items()
                    if param
                }
                parsed_delta = timedelta(**time_params)
    if parsed_delta is None:
        dt, result = fuzzy_datetime_parse(delta, sourceTime=datetime.min)
        if result:
            parsed_delta = dt - datetime.min
    if parsed_delta is None:
        msg = f"Duration is invalid: {delta}"
        raise ValueError(msg)
    return parsed_delta


def days_since_epoch(dt):
    __DAYS_IN_SECONDS__ = 24 * 60 * 60
    return calendar.timegm(dt.timetuple()) / __DAYS_IN_SECONDS__


def agenda_time_fmt(dt, military):
    hour_min_fmt = "%H:%M" if military else "%I:%M"
    ampm = "" if military else dt.strftime("%p").lower()
    return dt.strftime(hour_min_fmt).lstrip("0") + ampm


def is_all_day(event):
    # XXX: currently gcalcli represents all-day events as those that both begin
    # and end at midnight. This is ambiguous with Google Calendar events that
    # are not all-day but happen to begin and end at midnight.

    return (
        event["s"].hour == 0
        and event["s"].minute == 0
        and event["e"].hour == 0
        and event["e"].minute == 0
    )
