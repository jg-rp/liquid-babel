"""Date and time formatting filters for Python Liquid."""

from datetime import date
from datetime import datetime
from datetime import time

from typing import cast
from typing import Optional
from typing import Union

from babel import dates
from babel import Locale
from babel import UnknownLocaleError

from dateutil import parser

import pytz

from liquid import Context
from liquid.context import is_undefined

from liquid.exceptions import FilterArgumentError

from liquid.filter import liquid_filter
from liquid.filter import with_context


# pylint: disable=too-few-public-methods too-many-instance-attributes
@with_context
class DateTime:
    """A Liquid filter for formatting datetime objects.

    :param timezone_var: The name of a render context variable that resolves to
        a timezone. Defaults to `"timezone"`.
    :type timezone_var: str
    :param default_timezone: A fallback timezone to use if `timezone_var` can
        not be resolved. Defaults to `"UTC"`.
    :type default_timezone: str
    :param locale_var: The name of a render context variable that resolves to the
        current locale. Defaults to ``"locale"``.
    :type locale_var: str
    :param default_locale: A fallback locale to use if `locale_var` can not be
        resolved. Defaults to `"en_US"`.
    :type default_locale: str
    :param format_var: The name of a render context variable that resolves to the
        current datetime format string. Defaults to ``"datetime_format"``.
    :type format_var: str
    :param default_format: A fallback datetime format that is used if ``format_var``
        can not be resolved. Defaults to ``"medium"``.
    :type default_format: str
    :param input_timezone_var: The name of a render context variable that resolves to
        a timezone for parsing datetimes entered as strings. Defaults to `"input_timezone"`.
    :type input_timezone_var: str
    :param default_input_timezone: A fallback timezone to use if `input_timezone_var`
        can not be resolved. Defaults to `"UTC"`.
    :type default_input_timezone: str
    """

    formats = {
        "short": "short",
        "medium": "medium",
        "long": "long",
        "full": "full",
    }

    def __init__(
        self,
        *,
        timezone_var: str = "timezone",
        default_timezone: str = "UTC",
        locale_var: str = "locale",
        default_locale: str = "en_US",
        format_var: str = "datetime_format",
        default_format: str = "medium",
        input_timezone_var: str = "input_timezone",
        default_input_timezone: str = "UTC",
    ) -> None:
        self.timezone_var = timezone_var
        self.default_timezone = pytz.timezone(default_timezone)
        self.locale_var = locale_var
        self.default_locale = Locale.parse(default_locale)
        self.format_var = format_var
        self.default_format = self.formats.get(default_format, default_format)
        self.input_timezone_var = input_timezone_var
        self.default_input_timezone = pytz.timezone(default_input_timezone)

    # pylint: disable=redefined-builtin
    @liquid_filter
    def __call__(
        self,
        left: object,
        *,
        context: Context,
        format: Optional[str] = None,
    ) -> str:
        locale = self._resolve_locale(
            context,
            self.locale_var,
            default=self.default_locale,
        )

        if format:
            _format = self.formats.get(format, format)
        else:
            format_string = context.resolve(self.format_var)
            if is_undefined(format_string):
                _format = self.default_format
            else:
                _format = self.formats.get(format_string, format_string)

        tzinfo = self._resolve_timezone(
            context,
            self.timezone_var,
            default=self.default_timezone,
        )
        input_tzinfo = self._resolve_timezone(
            context,
            self.input_timezone_var,
            default=self.default_input_timezone,
        )

        return dates.format_datetime(
            _parse_datetime(left, input_tzinfo),
            format=_format,
            locale=locale,
            tzinfo=tzinfo,
        )

    def _resolve_locale(
        self,
        context: Context,
        locale_var: str,
        default: Locale,
    ) -> Locale:
        _locale = context.resolve(locale_var)
        if not is_undefined(_locale):
            try:
                locale = Locale.parse(_locale)
            except UnknownLocaleError:
                locale = default
        else:
            locale = default

        return cast(Locale, locale)

    def _resolve_timezone(
        self,
        context: Context,
        timezone_var: str,
        default: pytz.BaseTzInfo,
    ) -> pytz.BaseTzInfo:
        _tz = context.resolve(timezone_var)
        if not is_undefined(_tz):
            try:
                timezone: pytz.BaseTzInfo = pytz.timezone(_tz)
            except pytz.UnknownTimeZoneError:
                timezone = default
        else:
            timezone = default
        return timezone


def _parse_datetime(
    val: object,
    default_timezone: pytz.BaseTzInfo,
) -> Union[date, time, datetime, int, float, None]:
    if isinstance(val, str):
        if val in ("now", "today"):
            return None
        try:
            _dt = parser.parse(val)
            if _dt.tzinfo is None:
                return _dt.replace(tzinfo=default_timezone)
            return _dt
        except parser.ParserError as err:
            raise FilterArgumentError(str(err)) from err

    if not isinstance(val, (date, time, datetime, int, float)):
        raise FilterArgumentError(
            f"date expected date or time, found {type(val).__name__}"
        )

    return val
