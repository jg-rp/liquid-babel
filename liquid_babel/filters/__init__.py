# flake8: noqa
# pylint: disable=useless-import-alias,missing-module-docstring

from gettext import NullTranslations
from typing import Optional

from liquid import Environment
from liquid_babel.messages.translations import Translations

from .currency import Currency as Currency
from .date_and_time import DateTime as DateTime
from .number import Number as Number
from .translate import Translate
from .translate import GetText
from .translate import NGetText
from .translate import PGetText
from .translate import NPGetText


__all__ = [
    "Currency",
    "DateTime",
    "Number",
    "Translate",
    "GetText",
    "NGetText",
    "PGetText",
    "NPGetText",
    "currency",
    "number",
    "money",
    "money_with_currency",
    "money_without_currency",
    "money_without_trailing_zeros",
    "t",
    "gettext",
    "ngettext",
    "pgettext",
    "npgettext",
    "register_translation_filters",
]

# For convenience. Use defaults.
currency = Currency()
number = Number()

# For convenience. Something akin to Shopify's money filters.
money = currency
money_with_currency = Currency(default_format="¤#,##0.00 ¤¤")
money_without_currency = Currency(default_format="#,##0.00")
money_without_trailing_zeros = Currency(
    default_format="¤#,###",
    currency_digits=False,
)

# For convenience. Translation filters with default options.
t = Translate()
gettext = GetText()
ngettext = NGetText()
pgettext = PGetText()
npgettext = NPGetText()


def register_translation_filters(
    env: Environment,
    replace: bool = False,
    *,
    translations_var: str = "translations",
    default_translations: Optional[Translations] = None,
    message_interpolation: bool = True,
    autoescape_message: bool = False,
) -> None:
    """Add gettext-style translation filters to a Liquid environment.

    :param env: The liquid.Environment to add translation filters to.
    :type env: liquid.Environment.
    :param replace: If True, existing filters with conflicting names will
        be replaced. Defaults to False.
    :type replace: bool
    :param translations_var: The name of a render context variable that
        resolves to a gettext ``Translations`` class. Defaults to
        ``"translations"``.
    :type translations_var: str
    :param default_translations: A fallback translations class to use if
        ``translations_var`` can not be resolves. Defaults to
        ``NullTranslations``.
    :type default_translations: NullTranslations
    :param message_interpolation: If ``True`` (default), perform printf-style
        string interpolation on the translated message, using keyword arguments
        passed to the filter function.
    :type message_interpolation: bool
    :param autoescape_message: If `True` and the current environment has
        ``autoescape`` set to ``True``, the filter's left value will be escaped
        before translation. Defaults to ``False``.
    :type autoescape_message: bool
    """
    default_translations = default_translations or NullTranslations()
    default_filters = (
        Translate,
        GetText,
        NGetText,
        PGetText,
        NPGetText,
    )
    for _filter in default_filters:
        if replace or _filter.name not in env.filters:
            env.add_filter(
                _filter.name,
                _filter(  # type: ignore
                    translations_var=translations_var,
                    default_translations=default_translations,
                    message_interpolation=message_interpolation,
                    autoescape_message=autoescape_message,
                ),
            )
