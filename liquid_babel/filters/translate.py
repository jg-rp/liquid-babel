"""Translation filters."""
from gettext import NullTranslations

from typing import Any
from typing import cast
from typing import Optional
from typing import Tuple
from typing import Union

from liquid import Context
from liquid import Environment
from liquid import escape
from liquid import Markup

try:
    from liquid import soft_str  # type: ignore
except ImportError:
    # pylint: disable=invalid-name
    soft_str = str

from liquid.expression import Expression
from liquid.expression import Filter
from liquid.expression import StringLiteral

from liquid.filter import string_filter
from liquid.filter import int_arg

from liquid_babel.messages.translations import MessageText
from liquid_babel.messages.translations import TranslatableFilter
from liquid_babel.messages.translations import Translations

PGETTEXT_AVAILABLE = hasattr(NullTranslations, "pgettext")

__all__ = [
    "DEFAULT_KEYWORDS",
    "Translate",
    "GetText",
    "NGetText",
    "PGetText",
    "NPGetText",
    "register_translation_filters",
]

DEFAULT_KEYWORDS = {
    "translate": None,
    "t": None,
    "gettext": None,
    "ngettext": (1, 2),
    "pgettext": ((1, "c"), 2),
    "npgettext": ((1, "c"), 2, 3),
}


# pylint: disable=too-few-public-methods
class Translate(TranslatableFilter):
    """A Liquid filter for translating strings to other languages.

    Depending on the keyword arguments provided when the resulting filter
    is called, it could behave like gettext, ngettext, pgettext or npgettext.

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

    keywords = DEFAULT_KEYWORDS
    name = "t"
    with_context = True

    def __init__(
        self,
        *,
        translations_var: str = "translations",
        default_translations: Optional[Translations] = None,
        message_interpolation: bool = True,
        autoescape_message: bool = False,
    ) -> None:
        self.translations_var = translations_var
        self.default_translations = default_translations or NullTranslations()
        self.message_interpolation = message_interpolation
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
        translations = self._resolve_translations(context)

        # With Python 3.7, where pgettext is not available, the "context"
        # argument will be ignored.
        message_context = kwargs.pop("context", None)
        plural = kwargs.pop("plural", None)
        n = _count(kwargs.get("count"))

        if auto_escape and self.autoescape_message:
            left = escape(left)
            if plural is not None:
                plural = escape(plural)

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

        if self.message_interpolation:
            text = text % kwargs

        return text

    def message(
        self,
        left: Expression,
        _filter: Filter,
        lineno: int,
    ) -> Optional[MessageText]:
        if not isinstance(left, StringLiteral):
            return None

        _context = _filter.kwargs.get("context")
        plural = _filter.kwargs.get("plural")

        # Translate our filters into standard *gettext argument specs.

        if isinstance(plural, StringLiteral):
            funcname = "ngettext"
            message: Tuple[str, ...] = (left.value, plural.value)
        else:
            funcname = "gettext"
            message = (left.value,)

        if isinstance(_context, StringLiteral):
            funcname = "pgettext" if len(message) == 1 else "npgettext"
            message = (_context.value,) + message

        return MessageText(
            lineno=lineno,
            funcname=funcname,
            message=message,
        )

    def _resolve_translations(self, context: Context) -> Translations:
        return cast(
            Translations,
            context.resolve(self.translations_var, self.default_translations),
        )


class GetText(Translate):
    """A Liquid filter equivalent of `gettext.gettext`."""

    name = "gettext"

    @string_filter
    def __call__(
        self,
        left: str,
        *,
        context: Context,
        **kwargs: Any,
    ) -> str:
        auto_escape = context.env.autoescape
        translations = self._resolve_translations(context)

        if auto_escape and self.autoescape_message:
            left = escape(left)

        text = translations.gettext(left)

        if auto_escape:
            text = Markup(text)

        if self.message_interpolation:
            text = text % kwargs

        return text

    def message(
        self,
        left: Expression,
        _filter: Filter,
        lineno: int,
    ) -> Optional[MessageText]:
        if not isinstance(left, StringLiteral):
            return None

        return MessageText(
            lineno=lineno,
            funcname=self.name,
            message=(left.value,),
        )


class NGetText(GetText):
    """A Liquid filter equivalent of `gettext.ngettext`."""

    name = "ngettext"

    @string_filter
    def __call__(
        self,
        left: str,
        plural: str,
        count: object,
        *,
        context: Context,
        **kwargs: Any,
    ) -> str:
        auto_escape = context.env.autoescape
        translations = self._resolve_translations(context)
        count = int_arg(count, default=1)

        if auto_escape and self.autoescape_message:
            left = escape(left)
            plural = escape(plural)
        else:
            plural = soft_str(plural)

        text = translations.ngettext(left, plural, count)

        if auto_escape:
            text = Markup(text)

        if self.message_interpolation:
            text = text % kwargs

        return text

    def message(
        self,
        left: Expression,
        _filter: Filter,
        lineno: int,
    ) -> Optional[MessageText]:
        if len(_filter.args) < 1:
            return None

        plural = _filter.args[0]

        if not isinstance(left, StringLiteral) or not isinstance(plural, StringLiteral):
            return None

        return MessageText(
            lineno=lineno,
            funcname=self.name,
            message=(left.value, plural.value),
        )


class PGetText(Translate):
    """A Liquid filter equivalent of `gettext.pgettext`."""

    name = "pgettext"

    @string_filter
    def __call__(
        self,
        left: str,
        ctx: str,
        *,
        context: Context,
        **kwargs: Any,
    ) -> str:
        auto_escape = context.env.autoescape
        translations = self._resolve_translations(context)

        if auto_escape and self.autoescape_message:
            left = escape(left)
            ctx = escape(ctx)
        else:
            ctx = soft_str(ctx)

        text = translations.pgettext(ctx, left)

        if auto_escape:
            text = Markup(text)

        if self.message_interpolation:
            text = text % kwargs

        return text

    def message(
        self, left: Expression, _filter: Filter, lineno: int
    ) -> Optional[MessageText]:
        if len(_filter.args) < 1:
            return None

        ctx = _filter.args[0]

        if not isinstance(left, StringLiteral) or not isinstance(ctx, StringLiteral):
            return None

        return MessageText(
            lineno=lineno,
            funcname=self.name,
            message=(ctx.value, left.value),
        )


class NPGetText(Translate):
    """A Liquid filter equivalent of `gettext.npgettext`."""

    name = "npgettext"

    @string_filter
    def __call__(
        self,
        left: str,
        ctx: str,
        plural: str,
        count: object,
        *,
        context: Context,
        **kwargs: Any,
    ) -> str:
        auto_escape = context.env.autoescape
        translations = self._resolve_translations(context)
        count = int_arg(count, default=1)

        if auto_escape and self.autoescape_message:
            left = escape(left)
            ctx = escape(ctx)
            plural = escape(plural)
        else:
            ctx = soft_str(ctx)
            plural = soft_str(plural)

        text = translations.npgettext(ctx, left, plural, count)

        if auto_escape:
            text = Markup(text)

        if self.message_interpolation:
            text = text % kwargs

        return text

    def message(
        self,
        left: Expression,
        _filter: Filter,
        lineno: int,
    ) -> Optional[MessageText]:
        if len(_filter.args) < 2:
            return None

        ctx, plural = _filter.args[:2]

        if (
            not isinstance(left, StringLiteral)
            or not isinstance(plural, StringLiteral)
            or not isinstance(ctx, StringLiteral)
        ):
            return None

        return MessageText(
            lineno=lineno,
            funcname=self.name,
            message=(ctx.value, left.value, plural.value),
        )


def _count(val: Any) -> Union[int, None]:
    if val in (None, False, True):
        return None
    try:
        return int(val)
    except ValueError:
        return None


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
    for _filter in (Translate, GetText, NGetText, PGetText, NPGetText):
        if replace or _filter.name not in env.filters:
            env.add_filter(
                _filter.name,
                _filter(
                    translations_var=translations_var,
                    default_translations=default_translations,
                    message_interpolation=message_interpolation,
                    autoescape_message=autoescape_message,
                ),
            )
