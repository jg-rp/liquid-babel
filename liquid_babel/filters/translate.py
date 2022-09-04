"""A translation filter."""
import sys

from gettext import NullTranslations

from typing import Any
from typing import cast
from typing import Type
from typing import Union

from liquid import Context

from liquid.filter import string_filter
from liquid.filter import with_context

from markupsafe import escape
from markupsafe import Markup


PGETTEXT_AVAILABLE = sys.version_info[1] >= 3 and sys.version_info[1] > 8


# pylint: disable=too-few-public-methods
@with_context
class Translate:
    """A Liquid filter for translating string to other languages.

    :param translations_var: The name of a render context variable that
        resolves to a gettext ``Translations`` class. Defaults to
        ``"translations"``.
    :type translations_var: str
    :param default_translations: A fallback translations class to use if
        ``translations_var`` can not be resolves. Defaults to
        ``NullTranslations``.
    :type default_translations: NullTranslations
    :param c_style_interpolation: If ``True`` (default), perform c-style
        string interpolation on the translated message, using keyword arguments
        passed to the filter function.
    :type c_style_interpolation: bool
    :param autoescape_message: If `True` and the current environment has
        ``autoescape`` set to ``True``, the filter's left value will be escaped
        before translation. Defaults to ``False``.
    :type autoescape_message: bool
    """

    def __init__(
        self,
        *,
        translations_var: str = "translations",
        default_translations: Type[NullTranslations] = NullTranslations,
        c_style_interpolation: bool = True,
        autoescape_message: bool = False,
    ) -> None:
        self.translations_var = translations_var
        self.default_translations = default_translations
        self.c_style_interpolation = c_style_interpolation
        self.autoescape_message = autoescape_message

    @string_filter
    def __call__(
        self,
        left: str,
        *,
        context: Context,
        **kwargs: Any,
    ) -> str:
        auto_escape = context.env.autoescape

        message_context = kwargs.pop("context", None)
        plural = kwargs.pop("plural", None)
        n = _count(kwargs.get("count"))

        if auto_escape and self.autoescape_message:
            left = escape(left)
            if plural is not None:
                plural = escape(plural)

        translations = cast(
            NullTranslations,
            context.resolve(
                self.translations_var,
                default=self.default_translations,
            ),
        )

        if plural is not None and n is not None:
            if PGETTEXT_AVAILABLE and message_context is not None:
                text = translations.npgettext(
                    str(message_context),
                    left,
                    plural,
                    n,
                )
            else:
                text = translations.ngettext(left, plural, n)
        else:
            if PGETTEXT_AVAILABLE and message_context is not None:
                text = translations.pgettext(
                    str(message_context),
                    left,
                )

            else:
                text = translations.gettext(left)

        if auto_escape:
            text = Markup(text)

        if self.c_style_interpolation:
            text = text % kwargs

        return text


def _count(val: Any) -> Union[int, None]:
    if val in (None, False, True):
        return None
    try:
        return int(val)
    except ValueError:
        return None
