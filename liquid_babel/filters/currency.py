"""A currency filter for Python Liquid."""
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


# pylint: disable=too-few-public-methods
@with_context
class Currency:
    """A Liquid filter for formatting a currency value.

    :param context_currency_code: The name of a render context variable that resolves
        to the current currency code. Defaults to ``"currency_code"``.
    :type context_currency_code: str
    :param default_currency_code: A fallback currency code if ``context_currency_code``
        can not be resolved. Defaults to ``"USD"``.
    :type default_currency_code: str
    :param context_locale: The name of a render context variable that resolves to the
        current locale. Defaults to ``"locale"``.
    :type context_locale: str
    :param default_locale : A fallback locale to use if ``context_locale`` can not be
        resolved. Defaults to ``"en_US"``.
    :type default_locale: str
    :param context_format: The name of a render context variable that resolves to the
        current currency format string. Defaults to ``"currency_format"``.
    :type context_format: str
    :param default_format: A fallback currency format that is used if ``context_format``
        can not be resolved. Defaults to ``None``, which means the standard format for
        the current locale will be used.
    :type default_format: str | None
    """

    def __init__(
        self,
        *,
        context_currency_code: str = "currency_code",
        default_currency_code: str = "USD",
        context_locale: str = "locale",
        default_locale: str = "en_US",
        context_format: str = "currency_format",
        default_format: Optional[str] = None,
        currency_digits: bool = True,
    ) -> None:
        self.context_currency_code = context_currency_code
        self.default_currency_code = default_currency_code
        self.context_locale = context_locale
        self.default_locale = Locale.parse(default_locale)
        self.context_format = context_format
        self.default_format = default_format
        self.currency_digits = currency_digits

    @liquid_filter
    def __call__(
        self,
        left: object,
        *,
        context: Context,
        group_separator: bool = True,
    ) -> str:
        locale = self._resolve_local(context)
        _format = context.resolve(self.context_format, default=self.default_format)
        currency_code = context.resolve(
            self.context_currency_code,
            default=self.default_currency_code,
        )

        return cast(
            str,
            numbers.format_currency(
                _parse_decimal(left, locale),
                currency_code,
                format=_format,
                locale=locale,
                group_separator=group_separator,
                currency_digits=self.currency_digits,
            ),
        )

    def _resolve_local(self, context: Context) -> Locale:
        context_locale = context.resolve(self.context_locale)
        if not is_undefined(context_locale):
            try:
                locale = Locale.parse(context_locale)
            except UnknownLocaleError:
                locale = self.default_locale
        else:
            locale = self.default_locale

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
