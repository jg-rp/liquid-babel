"""A currency formatting filter for Python Liquid."""
from decimal import Decimal

from typing import cast
from typing import Optional
from typing import Union

from babel import numbers
from babel import Locale
from babel import UnknownLocaleError

from liquid import Context
from liquid.context import is_undefined

from liquid.filter import liquid_filter
from liquid.filter import num_arg
from liquid.filter import with_context


# pylint: disable=too-few-public-methods too-many-instance-attributes
@with_context
class Currency:
    """A Liquid filter for formatting currency values.

    :param currency_code_var: The name of a render context variable that resolves
        to the current currency code. Defaults to ``"currency_code"``.
    :type currency_code_var: str
    :param default_currency_code: A fallback currency code if ``currency_code_var``
        can not be resolved. Defaults to ``"USD"``.
    :type default_currency_code: str
    :param locale_var: The name of a render context variable that resolves to the
        current locale. Defaults to ``"locale"``.
    :type locale_var: str
    :param default_locale : A fallback locale to use if ``locale_var`` can not be
        resolved. Defaults to ``"en_US"``.
    :type default_locale: str
    :param format_var: The name of a render context variable that resolves to the
        current currency format string. Defaults to ``"currency_format"``.
    :type format_var: str
    :param default_format: A fallback currency format that is used if ``format_var``
        can not be resolved. Defaults to ``None``, which means the standard format for
        the current locale will be used.
    :type default_format: str | None
    :param currency_digits: Indicates if the format should override locale specific
        trailing digit behavior. Defaults to ``False``.
    :type currency_digits: bool
    :param input_locale_var: The name of a render context variable that resolves to
        a locale suitable for parsing input strings to decimals. Defaults to
        ``"input_locale"``.
    :type input_locale_var: str
    :param default_input_locale: A fallback locale to use if ``input_locale_var``
        can not be resolved. Defaults to ``"en_US"``.
    """

    def __init__(
        self,
        *,
        currency_code_var: str = "currency_code",
        default_currency_code: str = "USD",
        locale_var: str = "locale",
        default_locale: str = "en_US",
        format_var: str = "currency_format",
        default_format: Optional[str] = None,
        currency_digits: bool = True,
        input_locale_var: str = "input_locale",
        default_input_locale: str = "en_US",
    ) -> None:
        self.currency_code_var = currency_code_var
        self.default_currency_code = default_currency_code
        self.locale_var = locale_var
        self.default_locale = Locale.parse(default_locale)
        self.format_var = format_var
        self.default_format = default_format
        self.currency_digits = currency_digits
        self.input_locale_var = input_locale_var
        self.default_input_locale = Locale.parse(default_input_locale)

    @liquid_filter
    def __call__(
        self,
        left: object,
        *,
        context: Context,
        group_separator: bool = True,
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
        _format = context.resolve(self.format_var, default=self.default_format)
        currency_code = context.resolve(
            self.currency_code_var,
            default=self.default_currency_code,
        )

        return cast(
            str,
            numbers.format_currency(
                _parse_decimal(left, input_locale),
                currency_code,
                format=_format,
                locale=locale,
                group_separator=group_separator,
                currency_digits=self.currency_digits,
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
