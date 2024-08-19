class GcalcliError(Exception):
    pass


class ValidationError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)
        self.message = message


class ReadonlyError(Exception):
    def __init__(self, fieldname, message) -> None:
        message = f"Field {fieldname} is read-only. {message}"
        super().__init__(message)


class ReadonlyCheckError(ReadonlyError):
    _fmt = 'Current value "{}" does not match update value "{}"'

    def __init__(self, fieldname, curr_value, mod_value) -> None:
        message = self._fmt.format(curr_value, mod_value)
        super().__init__(fieldname, message)


def raise_one_cal_error(cals):
    msg = f"You must only specify a single calendar\nCalendars: {cals}\n"
    raise GcalcliError(msg)
