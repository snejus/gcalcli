import re
from typing import Callable

from .exceptions import ValidationError
from .printer import Printer
from .utils import REMINDER_REGEX, get_time_from_str, get_timedelta_from_str

# TODO: in the future, pull these from the API
# https://developers.google.com/calendar/v3/reference/colors
VALID_OVERRIDE_COLORS = [
    "lavender",
    "sage",
    "grape",
    "flamingo",
    "banana",
    "tangerine",
    "peacock",
    "graphite",
    "blueberry",
    "basil",
    "tomato",
]


def get_override_color_id(color):
    return str(VALID_OVERRIDE_COLORS.index(color) + 1)


def get_input(printer, prompt, validator_func) -> str:
    printer.msg(prompt, "magenta")
    while True:
        try:
            return validate_input(validator_func)
        except ValidationError as e:
            printer.msg(e.message, "red")
            printer.msg(prompt, "magenta")


def color_validator(input_str):
    """A filter allowing only the particular colors used by the Google Calendar
    API.

    Raises ValidationError otherwise.
    """
    try:
        assert input_str in {*VALID_OVERRIDE_COLORS, ""}
        return input_str
    except AssertionError as e:
        raise ValidationError(
            "Expected colors are: "
            + ", ".join(VALID_OVERRIDE_COLORS)
            + ". (Ctrl-C to exit)\n"
        ) from e


def str_to_int_validator(input_str):
    """A filter allowing any string which can be
    converted to an int.
    Raises ValidationError otherwise.
    """
    try:
        int(input_str)
        return input_str
    except ValueError as e:
        raise ValidationError("Input here must be a number. (Ctrl-C to exit)\n") from e


def parsable_date_validator(input_str):
    """A filter allowing any string which can be parsed
    by dateutil.
    Raises ValidationError otherwise.
    """
    try:
        get_time_from_str(input_str)
        return input_str
    except ValueError as e:
        raise ValidationError(
            "Expected format: a date (e.g. 2019-01-01, tomorrow 10am, "
            "2nd Jan, Jan 4th, etc) or valid time if today. "
            "(Ctrl-C to exit)\n"
        ) from e


def parsable_duration_validator(input_str):
    """A filter allowing any duration string which can be parsed
    by parsedatetime.
    Raises ValidationError otherwise.
    """
    try:
        get_timedelta_from_str(input_str)
        return input_str
    except ValueError as e:
        raise ValidationError(
            "Expected format: a duration (e.g. 1m, 1s, 1h3m)(Ctrl-C to exit)\n"
        ) from e


def str_allow_empty_validator(input_str):
    """A simple filter that allows any string to pass.
    Included for completeness and for future validation if required.
    """
    return input_str


def non_blank_str_validator(input_str):
    """A simple filter allowing string len > 1 and not None
    Raises ValidationError otherwise.
    """
    if input_str in {None, ""}:
        raise ValidationError("Input here cannot be empty. (Ctrl-C to exit)\n")
    return input_str


def reminder_validator(input_str):
    """Allows a string that matches utils.REMINDER_REGEX.
    Raises ValidationError otherwise.
    """
    match = re.match(REMINDER_REGEX, input_str)
    if match or input_str == ".":
        return input_str
    raise ValidationError(
        "Expected format: <number><w|d|h|m> <popup|email|sms>. (Ctrl-C to exit)\n"
    )


def validate_input(validator_func: Callable[[str], str]) -> str:
    """Wrapper around Validator funcs."""
    inp_str = input()
    return validator_func(inp_str)


def get_title(printer: Printer) -> str:
    return get_input(printer, "Title: ", STR_NOT_EMPTY).strip()


def get_reminder(printer: Printer) -> str:
    return get_input(printer, "Enter a valid reminder or '.' to end: ", REMINDER)


def get_duration(printer: Printer, allday: bool = False) -> str:
    prompt = "Duration (days): " if allday else "Duration (human readable): "
    return get_input(printer, prompt, PARSABLE_DURATION)


def get_start_dt(printer: Printer) -> str:
    return get_input(printer, "When: ", PARSABLE_DATE).strip()


def get_location(printer: Printer) -> str:
    return get_input(printer, "Location: ", STR_ALLOW_EMPTY).strip()


def get_desc(printer: Printer) -> str:
    return get_input(printer, "Description: ", STR_ALLOW_EMPTY).strip()


def get_color(printer: Printer) -> str:
    return get_input(printer, "Color: ", VALID_COLORS)


STR_NOT_EMPTY = non_blank_str_validator
STR_ALLOW_EMPTY = str_allow_empty_validator
STR_TO_INT = str_to_int_validator
PARSABLE_DATE = parsable_date_validator
PARSABLE_DURATION = parsable_duration_validator
VALID_COLORS = color_validator
REMINDER = reminder_validator
