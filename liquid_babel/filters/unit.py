"""A measurement units formatting filter for Python Liquid."""
from __future__ import annotations

from decimal import Decimal
from functools import wraps

from typing import Any
from typing import Callable
from typing import cast
from typing import Optional
from typing import Union
from typing import TYPE_CHECKING

from babel import Locale
from babel import numbers
from babel import UnknownLocaleError
from babel import units


from liquid import Context
from liquid.context import is_undefined
from liquid.exceptions import FilterArgumentError
from liquid.filter import num_arg

if TYPE_CHECKING:  # pragma: no cover
    FilterT = Callable[..., Any]


def unit_filter(_filter: FilterT) -> FilterT:
    """A filter function decorator that handles `TypeError` and `UnknownUnitError`."""

    @wraps(_filter)
    def wrapper(val: object, *args: Any, **kwargs: Any) -> Any:
        try:
            return _filter(val, *args, **kwargs)
        except (TypeError, units.UnknownUnitError) as err:
            raise FilterArgumentError(err) from err

    return wrapper


# pylint: disable=too-few-public-methods too-many-instance-attributes
class Unit:
    """A Liquid filter for formatting units of measurement.

    :param locale_var: The name of a render context variable that resolves to the
        current locale. Defaults to ``"locale"``.
    :type locale_var: str
    :param default_locale: A fallback locale to use if ``locale_var`` can not be
        resolved. Defaults to ``"en_US"``.
    :type default_locale: str
    :param length_var: The name of a render context variable that resolves to a
        unit format length. Should be one of "short", "long" or "narrow".
        Defaults to ``"long"``.
    :type length_var: str
    :param default_length: A fallback format length to use if ``length_var`` can
        not be resolved.
    :type default_length: str
    :param format_var: The name of a render context variable that resolves to a
        decimal format string. Defaults to ``"unit_format"``.
    :type format_var: str
    :param default_format: A fallback decimal format to use if ``format_var`` can
        not be resolved. Defaults to ``None``, meaning the locale's standard
        decimal format is used.
    :type default_format: str | None
    :param input_locale_var: The name of a render context variable that resolves to
        a locale suitable for parsing input strings to decimals. Defaults to
        ``"input_locale"``.
    :type input_locale_var: str
    :param default_input_locale: A fallback locale to use if ``input_locale_var``
        can not be resolved. Defaults to ``"en_US"``.
    :type default_input_locale: str
    """

    with_context = True

    def __init__(
        self,
        *,
        locale_var: str = "locale",
        default_locale: str = "en_US",
        length_var: str = "unit_length",
        default_length: str = "long",
        format_var: str = "unit_format",
        default_format: Optional[str] = None,
        input_locale_var: str = "input_locale",
        default_input_locale: str = "en_US",
    ) -> None:
        self.locale_var = locale_var
        self.default_locale = Locale.parse(default_locale)
        self.length_var = length_var
        self.default_length = default_length
        self.format_var = format_var
        self.default_format = default_format
        self.input_locale_var = input_locale_var
        self.default_input_locale = Locale.parse(default_input_locale)

    # pylint: disable=redefined-builtin
    @unit_filter
    def __call__(
        self,
        left: object,
        measurement_unit: str,
        *,
        context: Context,
        denominator: object = None,
        denominator_unit: Optional[str] = None,
        length: Optional[str] = None,
        format: Optional[str] = None,
    ) -> str:
        locale = self._resolve_locale(
            context,
            self.locale_var,
            default=self.default_locale,
        )
        input_locale = self._resolve_locale(
            context,
            self.input_locale_var,
            default=self.default_input_locale,
        )

        if length:
            _length = length
        else:
            _length = context.resolve(self.length_var)

        if _length not in ("short", "long", "narrow"):
            _length = self.default_length

        if format:
            _format: Optional[str] = format
        else:
            format_string = context.resolve(self.format_var)
            if is_undefined(format_string):
                _format = self.default_format
            else:
                _format = format_string

        if denominator is not None or denominator_unit is not None:
            _denominator = (
                _parse_decimal(denominator, input_locale)
                if denominator is not None
                else 1
            )
            return cast(
                str,
                units.format_compound_unit(
                    _parse_decimal(left, input_locale),
                    numerator_unit=measurement_unit,
                    denominator_value=_denominator,  # type: ignore
                    denominator_unit=denominator_unit,
                    length=_length,
                    format=_format,
                    locale=locale,
                ),
            )

        return cast(
            str,
            units.format_unit(
                _parse_decimal(left, input_locale),
                measurement_unit=measurement_unit,
                length=_length,
                format=_format,
                locale=locale,
            ),
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


def _parse_decimal(val: object, locale: Union[str, Locale]) -> Decimal:
    if isinstance(val, str):
        try:
            return cast(Decimal, numbers.parse_decimal(val, locale))
        except numbers.NumberFormatError:
            return Decimal(0)

    if isinstance(val, (Decimal, float, int)):
        return Decimal(val)

    # Give objects that implement __int__ etc. a chance.
    return Decimal(num_arg(val, 0))
