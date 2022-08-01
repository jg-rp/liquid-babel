"""A decimal formatting filter for Python Liquid."""
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
class Number:
    """A Liquid filter for formatting decimal values.

    :param decimal_quantization_var: The name of a render context variable that
        resolves to the decimal quantization to be used. Defaults to
        ``"decimal_quantization"``.
    :type decimal_quantization_var: str
    :param default_decimal_quantization: A fallback decimal quantization if
        ``decimal_quantization_var`` can not be resolved. Defaults to ``False``.
    :type default_decimal_quantization: bool
    :param locale_var: The name of a render context variable that resolves to the
        current locale. Defaults to ``"locale"``.
    :type locale_var: str
    :param default_locale: A fallback locale to use if `locale_var` can not be
        resolved. Defaults to `"en_US"`.
    :type default_locale: str
    :param format_var: The name of a render context variable that resolves to the
        current decimal format string. Defaults to ``"decimal_format"``.
    :type format_var: str
    :param default_format: A fallback decimal format that is used if ``format_var``
        can not be resolved. Defaults to ``None``, which means the standard format for
        the current locale will be used.
    :type default_format: str | None
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
        decimal_quantization_var: str = "decimal_quantization",
        default_decimal_quantization: bool = False,
        locale_var: str = "locale",
        default_locale: str = "en_US",
        format_var: str = "decimal_format",
        default_format: Optional[str] = None,
        input_locale_var: str = "input_locale",
        default_input_locale: str = "en_US",
    ) -> None:
        self.decimal_quantization_var = decimal_quantization_var
        self.default_decimal_quantization = default_decimal_quantization
        self.locale_var = locale_var
        self.default_locale = Locale.parse(default_locale)
        self.format_var = format_var
        self.default_format = default_format
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
        decimal_quantization = context.resolve(
            self.decimal_quantization_var,
            default=self.default_decimal_quantization,
        )
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

        return cast(
            str,
            numbers.format_decimal(
                _parse_decimal(left, input_locale),
                format=_format,
                locale=locale,
                group_separator=group_separator,
                decimal_quantization=decimal_quantization,
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
