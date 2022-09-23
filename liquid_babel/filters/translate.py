"""Translation filters."""
import re

from abc import ABC
from abc import abstractmethod

from gettext import NullTranslations

from typing import Any
from typing import cast
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Type
from typing import Union

from liquid import Context
from liquid import Environment
from liquid import Markup

from liquid.expression import Expression
from liquid.expression import Filter
from liquid.expression import StringLiteral

from liquid.filter import liquid_filter
from liquid.filter import int_arg

from liquid_babel.messages.translations import MessageText
from liquid_babel.messages.translations import TranslatableFilter
from liquid_babel.messages.translations import Translations
from liquid_babel.messages.translations import to_liquid_string

PGETTEXT_AVAILABLE = hasattr(NullTranslations, "pgettext")

__all__ = [
    "Translate",
    "GetText",
    "NGetText",
    "PGetText",
    "NPGetText",
    "register_translation_filters",
]


class BaseTranslateFilter(ABC):
    """Base class for the default translation filters."""

    name = "base"
    re_vars = re.compile(r"(?<!%)%\((\w+)\)s")
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

    @abstractmethod
    def __call__(
        self,
        left: object,
        *,
        context: Context,
        **kwargs: Any,
    ) -> str:
        """Filter function definition."""

    def format_message(
        self, context: Context, message_text: str, message_vars: Dict[str, Any]
    ) -> str:
        """Return the message string formatted with the given message variables."""
        with context.extend(namespace=message_vars):
            _vars = {
                k: to_liquid_string(context.resolve(k), context.env.autoescape)
                for k in self.re_vars.findall(message_text)
            }

        # Missing variables get replaced by the current `Undefined` type and we're
        # converting all values to a string, so a KeyError or a ValueError should
        # be impossible.
        return message_text % _vars

    def _resolve_translations(self, context: Context) -> Translations:
        return cast(
            Translations,
            context.resolve(self.translations_var, self.default_translations),
        )


# pylint: disable=too-few-public-methods
class Translate(BaseTranslateFilter, TranslatableFilter):
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

    name = "t"

    @liquid_filter
    def __call__(
        self,
        __left: object,
        __message_context: object = None,
        *,
        context: Context,
        **kwargs: Any,
    ) -> str:
        auto_escape = context.env.autoescape
        __left = to_liquid_string(
            __left,
            autoescape=auto_escape and self.autoescape_message,
        )
        translations = self._resolve_translations(context)

        # With Python 3.7, where pgettext is not available, the "context"
        # argument will be ignored.
        message_context = __message_context or None
        plural = kwargs.pop("plural", None)
        n = _count(kwargs.get("count"))

        if plural is not None and n is not None:
            plural = to_liquid_string(
                plural,
                autoescape=auto_escape and self.autoescape_message,
            )

            if PGETTEXT_AVAILABLE and message_context is not None:
                text = translations.npgettext(
                    str(message_context),
                    __left,
                    plural,
                    n,
                )
            else:
                text = translations.ngettext(__left, plural, n)
        else:
            if PGETTEXT_AVAILABLE and message_context is not None:
                text = translations.pgettext(
                    str(message_context),
                    __left,
                )

            else:
                text = translations.gettext(__left)

        if auto_escape:
            text = Markup(text)

        if self.message_interpolation:
            text = self.format_message(context, text, kwargs)

        return text

    def message(
        self,
        left: Expression,
        _filter: Filter,
        lineno: int,
    ) -> Optional[MessageText]:
        if not isinstance(left, StringLiteral):
            return None

        _context = _filter.args[0] if _filter.args else None
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
            return MessageText(
                lineno=lineno,
                funcname=funcname,
                message=((_context.value, "c"),) + message,
            )

        return MessageText(
            lineno=lineno,
            funcname=funcname,
            message=message,
        )


class GetText(BaseTranslateFilter, TranslatableFilter):
    """A Liquid filter equivalent of `gettext.gettext`."""

    name = "gettext"

    @liquid_filter
    def __call__(
        self,
        __left: object,
        *,
        context: Context,
        **kwargs: Any,
    ) -> str:
        auto_escape = context.env.autoescape
        __left = to_liquid_string(
            __left,
            autoescape=auto_escape and self.autoescape_message,
        )

        translations = self._resolve_translations(context)
        text = translations.gettext(__left)

        if auto_escape:
            text = Markup(text)

        if self.message_interpolation:
            text = self.format_message(context, text, kwargs)

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

    @liquid_filter
    def __call__(
        self,
        __left: object,
        __plural: str,
        __count: object,
        *,
        context: Context,
        **kwargs: Any,
    ) -> str:
        auto_escape = context.env.autoescape
        __left = to_liquid_string(
            __left,
            autoescape=auto_escape and self.autoescape_message,
        )

        __plural = to_liquid_string(
            __plural,
            autoescape=auto_escape and self.autoescape_message,
        )

        __count = int_arg(__count, default=1)

        translations = self._resolve_translations(context)
        text = translations.ngettext(__left, __plural, __count)

        if auto_escape:
            text = Markup(text)

        if self.message_interpolation:
            text = self.format_message(context, text, kwargs)

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


class PGetText(BaseTranslateFilter, TranslatableFilter):
    """A Liquid filter equivalent of `gettext.pgettext`."""

    name = "pgettext"

    @liquid_filter
    def __call__(
        self,
        __left: object,
        __message_context: str,
        *,
        context: Context,
        **kwargs: Any,
    ) -> str:
        auto_escape = context.env.autoescape
        __left = to_liquid_string(
            __left,
            autoescape=auto_escape and self.autoescape_message,
        )

        __message_context = to_liquid_string(
            __message_context,
            autoescape=auto_escape and self.autoescape_message,
        )

        translations = self._resolve_translations(context)
        text = translations.pgettext(__message_context, __left)

        if auto_escape:
            text = Markup(text)

        if self.message_interpolation:
            text = self.format_message(context, text, kwargs)

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
            message=((ctx.value, "c"), left.value),
        )


class NPGetText(BaseTranslateFilter, TranslatableFilter):
    """A Liquid filter equivalent of `gettext.npgettext`."""

    name = "npgettext"

    @liquid_filter
    def __call__(
        self,
        __left: object,
        __message_context: str,
        __plural: str,
        __count: object,
        *,
        context: Context,
        **kwargs: Any,
    ) -> str:
        auto_escape = context.env.autoescape
        __left = to_liquid_string(
            __left,
            autoescape=auto_escape and self.autoescape_message,
        )

        __message_context = to_liquid_string(
            __message_context,
            autoescape=auto_escape and self.autoescape_message,
        )

        __plural = to_liquid_string(
            __plural,
            autoescape=auto_escape and self.autoescape_message,
        )

        __count = int_arg(__count, default=1)

        translations = self._resolve_translations(context)
        text = translations.npgettext(
            __message_context,
            __left,
            __plural,
            __count,
        )

        if auto_escape:
            text = Markup(text)

        if self.message_interpolation:
            text = self.format_message(context, text, kwargs)

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
            message=((ctx.value, "c"), left.value, plural.value),
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
    default_filters: Tuple[Type[BaseTranslateFilter], ...] = (
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
                _filter(
                    translations_var=translations_var,
                    default_translations=default_translations,
                    message_interpolation=message_interpolation,
                    autoescape_message=autoescape_message,
                ),
            )
