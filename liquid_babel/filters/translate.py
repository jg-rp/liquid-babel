"""A translation filter."""
import sys

from gettext import NullTranslations

from typing import Any
from typing import cast
from typing import Optional
from typing import Tuple
from typing import Union

from liquid import Context
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

from liquid_babel.messages.extract import MessageText
from liquid_babel.messages.extract import TranslatableFilter
from liquid_babel.messages.translations import Translations

PGETTEXT_AVAILABLE = sys.version_info[1] >= 3 and sys.version_info[1] > 8


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
    :param message_interpolation: If ``True`` (default), perform sprintf-style
        string interpolation on the translated message, using keyword arguments
        passed to the filter function.
    :type message_interpolation: bool
    :param autoescape_message: If `True` and the current environment has
        ``autoescape`` set to ``True``, the filter's left value will be escaped
        before translation. Defaults to ``False``.
    :type autoescape_message: bool
    """

    keywords = {
        "translate": None,
        "t": None,
        "gettext": None,
        "ngettext": (1, 2),
        "pgettext": ((1, "c"), 2),
        "npgettext": ((1, "c"), 2, 3),
    }

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
            funcname="gettext",
            message=(left.value,),
        )


class NGetText(GetText):
    """A Liquid filter equivalent of `gettext.ngettext`."""

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
            funcname="ngettext",
            message=(left.value, plural.value),
        )


class PGetText(Translate):
    """A Liquid filter equivalent of `gettext.pgettext`."""

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
            funcname="pgettext",
            message=(ctx.value, left.value),
        )


class NPGetText(Translate):
    """A Liquid filter equivalent of `gettext.npgettext`."""

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
            funcname="ngettext",
            message=(ctx.value, left.value, plural.value),
        )


def _count(val: Any) -> Union[int, None]:
    if val in (None, False, True):
        return None
    try:
        return int(val)
    except ValueError:
        return None
