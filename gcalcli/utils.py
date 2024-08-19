from __future__ import annotations

import calendar
import locale
import re
import time
from datetime import datetime, timedelta

from dateutil.parser import parse as dateutil_parse
from dateutil.tz import tzlocal
from durations_nlp import Duration
from parsedatetime.parsedatetime import Calendar

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


def get_time_from_str(datestr: str) -> datetime:
    """Convert a string to a time: first uses the dateutil parser, falls back
    on fuzzy matching with parsedatetime.
    """
    zero_oclock_today = datetime.now(tzlocal()).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    try:
        return dateutil_parse(datestr, default=zero_oclock_today)
    except ValueError as e:
        struct, result = fuzzy_date_parse(datestr)
        if not result:
            msg = f"Date and time is invalid: {datestr}"
            raise ValueError(msg) from e

        return datetime.fromtimestamp(time.mktime(struct), tzlocal())


def get_timedelta_from_str(duration_str: str) -> timedelta:
    """Parse a time string a timedelta object.
    Formats:
      - number -> duration in minutes
      - "1:10" -> hour and minutes
      - "1d 1h 1m" -> days, hours, minutes
    Based on https://stackoverflow.com/a/51916936/12880.
    """
    try:
        return timedelta(seconds=Duration(duration_str).to_seconds())
    except Exception as e:
        msg = f"Duration time is invalid: {duration_str}\n"
        raise ValueError(msg) from e


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
