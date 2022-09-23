"""Tag and node definition for the "trans" or "translate" tag."""
from __future__ import annotations

import itertools
import re
import sys

from functools import partial
from gettext import NullTranslations

from typing import Any
from typing import TYPE_CHECKING
from typing import cast
from typing import Dict
from typing import Iterable
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import TextIO
from typing import Tuple

from liquid import Markup

from liquid.ast import ChildNode
from liquid.ast import Node
from liquid.ast import BlockNode

from liquid.builtin.literal import LiteralNode
from liquid.builtin.statement import StatementNode

from liquid.expression import FilteredExpression
from liquid.expression import Identifier
from liquid.expression import IdentifierPathElement
from liquid.expression import StringLiteral

from liquid.limits import to_int

from liquid.lex import include_expression_rules
from liquid.lex import _compile_rules
from liquid.lex import _tokenize

from liquid.parse import expect
from liquid.parse import get_parser
from liquid.parse import parse_expression
from liquid.parse import parse_unchained_identifier

from liquid.stream import TokenStream
from liquid.tag import Tag

from liquid.token import Token
from liquid.token import TOKEN_TAG
from liquid.token import TOKEN_EXPRESSION
from liquid.token import TOKEN_TRUE
from liquid.token import TOKEN_FALSE
from liquid.token import TOKEN_NIL
from liquid.token import TOKEN_NULL
from liquid.token import TOKEN_COLON
from liquid.token import TOKEN_AS
from liquid.token import TOKEN_EOF
from liquid.token import TOKEN_COMMA

from liquid_babel.messages.exceptions import TranslationSyntaxError

from liquid_babel.messages.translations import MessageText
from liquid_babel.messages.translations import TranslatableTag
from liquid_babel.messages.translations import Translations
from liquid_babel.messages.translations import to_liquid_string

if TYPE_CHECKING:  # pragma: no cover
    from liquid.context import Context
    from liquid import Environment
    from liquid.expression import Expression


TAG_TRANS = sys.intern("translate")
TAG_ENDTRANS = sys.intern("endtranslate")
TAG_PLURAL = sys.intern("plural")

trans_expression_keywords = frozenset(
    [
        TOKEN_TRUE,
        TOKEN_FALSE,
        TOKEN_NIL,
        TOKEN_NULL,
        TOKEN_AS,
    ]
)

tokenize_trans_expression = partial(
    _tokenize,
    rules=_compile_rules(include_expression_rules),
    keywords=trans_expression_keywords,
)


class TransKeywordArg(NamedTuple):
    """A key/expression pair representing a block keyword argument."""

    name: str
    expr: Expression


class MessageBlock(NamedTuple):
    """The AST block, text and placeholder variables representing a message block."""

    block: BlockNode
    text: str
    vars: List[str]


class TranslateTag(Tag):
    """The "Trans" or "Translate" tag."""

    name = TAG_TRANS
    end = TAG_ENDTRANS
    block = True
    plural_name = TAG_PLURAL
    re_whitespace = re.compile(r"\s*\n\s*")
    trim_messages = True

    def __init__(self, env: Environment):
        super().__init__(env)
        self.parser = get_parser(self.env)

    def parse(self, stream: TokenStream) -> TranslateNode:
        expect(stream, TOKEN_TAG, value=self.name)
        tok = stream.current
        stream.next_token()
        args = {}

        if stream.current.type == TOKEN_EXPRESSION:
            expr_stream = TokenStream(tokenize_trans_expression(stream.current.value))
            while expr_stream.current.type != TOKEN_EOF:
                key, expr = self.parse_argument(expr_stream)
                args[key] = expr

                if expr_stream.current.type == TOKEN_COMMA:
                    expr_stream.next_token()  # Eat comma

            stream.next_token()

        message_block = self.parser.parse_block(stream, (self.end, self.plural_name))
        singular = self.parse_message_block(message_block)

        if (
            stream.current.type == TOKEN_TAG
            and stream.current.value == self.plural_name
        ):
            stream.next_token()
            plural_block = self.parser.parse_block(stream, (self.end,))
            plural = self.parse_message_block(plural_block)
        else:
            plural = None

        expect(stream, TOKEN_TAG, value=self.end)

        return TranslateNode(
            tok=tok,
            args=args,
            singular=singular,
            plural=plural,
        )

    def parse_argument(self, stream: TokenStream) -> TransKeywordArg:
        """Parse a keyword argument from a stream of tokens."""
        key = str(parse_unchained_identifier(stream))
        stream.next_token()

        expect(stream, TOKEN_COLON)
        stream.next_token()  # Eat colon

        val = parse_expression(stream)
        stream.next_token()

        return TransKeywordArg(key, val)

    def parse_message_block(self, block: BlockNode) -> MessageBlock:
        """Return message text and variables from a translation block."""
        message_text: List[str] = []
        message_vars: List[str] = []
        for node in block.statements:
            if isinstance(node, LiteralNode):
                message_text.append(node.tok.value.replace("%", "%%"))
            elif isinstance(node, StatementNode):
                if (
                    isinstance(node.expression, FilteredExpression)
                    and isinstance(node.expression.expression, Identifier)
                    and isinstance(
                        node.expression.expression.path[0], IdentifierPathElement
                    )
                    and isinstance(node.expression.expression.path[0].value, str)
                ):
                    if len(node.expression.expression.path) > 1:
                        raise TranslationSyntaxError(
                            f"unexpected variable property access '{node.expression.expression}'",
                            linenum=node.token().linenum,
                        )

                    var = node.expression.expression.path[0].value
                    if node.expression.filters:
                        raise TranslationSyntaxError(
                            f"unexpected filter on translation variable '{var}'",
                            linenum=node.token().linenum,
                        )
                    message_text.append(f"%({var})s")
                    message_vars.append(var)
                else:
                    raise TranslationSyntaxError(
                        f"expected a translation variable, found '{node.expression}'",
                        linenum=node.token().linenum,
                    )
            else:
                raise TranslationSyntaxError(
                    f"unexpected tag '{node.token().value}' in translation text",
                    linenum=node.token().linenum,
                )

        msg = "".join(message_text)
        if self.trim_messages:
            msg = self.re_whitespace.sub(" ", msg.strip())

        return MessageBlock(block, msg, message_vars)


class TranslateNode(Node, TranslatableTag):
    """Parse tree node for the Translation block tag."""

    __slots__ = (
        "tok",
        "args",
        "singular",
        "singular_block",
        "singular_vars",
        "plural",
    )

    default_translations = NullTranslations()
    translations_var = "translations"
    message_count_var = "count"
    message_context_var = "context"
    re_vars = re.compile(r"(?<!%)%\((\w+)\)s")

    def __init__(
        self,
        tok: Token,
        *,
        args: Dict[str, Expression],
        singular: MessageBlock,
        plural: Optional[MessageBlock],
    ):
        self.tok = tok
        self.args = args
        self.singular_block, self.singular, self.singular_vars = singular
        self.plural = plural

    def render_to_output(
        self,
        context: Context,
        buffer: TextIO,
    ) -> Optional[bool]:
        translations = self.resolve_translations(context)
        namespace = {k: v.evaluate(context) for k, v in self.args.items()}
        count = self.resolve_count(context, namespace)
        message_context = self.resolve_message_context(context, namespace)

        with context.extend(namespace):
            message_text, _vars = self.gettext(
                translations,
                count=count,
                message_context=message_context,
            )
            message_vars = {v: context.resolve(v) for v in _vars}

        buffer.write(self.format_message(context, message_text, message_vars))
        return True

    async def render_to_output_async(
        self,
        context: Context,
        buffer: TextIO,
    ) -> Optional[bool]:
        translations = self.resolve_translations(context)
        namespace = {k: await v.evaluate_async(context) for k, v in self.args.items()}
        count = self.resolve_count(context, namespace)
        message_context = self.resolve_message_context(context, namespace)

        with context.extend(namespace):
            message_text, _vars = self.gettext(
                translations,
                count=count,
                message_context=message_context,
            )
            message_vars = {v: context.resolve(v) for v in _vars}

        buffer.write(self.format_message(context, message_text, message_vars))
        return True

    def resolve_translations(self, context: Context) -> Translations:
        """Return a translations object from the current render context."""
        return cast(
            Translations,
            context.resolve(self.translations_var, self.default_translations),
        )

    def resolve_count(
        self,
        context: Context,  # pylint: disable=unused-argument
        block_scope: Dict[str, object],
    ) -> Optional[int]:
        """Return a message count, if any, using the current render context and/or
        the translation's block scope."""
        try:
            return to_int(block_scope.get(self.message_count_var, 1))  # defaults to 1
        except ValueError:
            return 1

    def resolve_message_context(
        self,
        context: Context,  # pylint: disable=unused-argument
        block_scope: Dict[str, object],
    ) -> Optional[str]:
        """Return the message context string, if any, using the current render
        context and/or the translation block scope."""
        message_context = block_scope.pop(self.message_context_var, None)
        if message_context:
            return (
                str(message_context)
                if not isinstance(message_context, str)
                else message_context
            )  # Just in case we get a Markupsafe object.
        return None

    def gettext(
        self,
        translations: Translations,
        count: Optional[int],
        message_context: Optional[str],
    ) -> Tuple[str, Iterable[str]]:
        """Get translated text from the given translations object."""
        if self.plural and count:
            if message_context:
                text = translations.npgettext(
                    message_context, self.singular, self.plural.text, count
                )
            else:
                text = translations.ngettext(self.singular, self.plural.text, count)
            return text, itertools.chain(self.singular_vars, self.plural.vars)

        if message_context:
            text = translations.pgettext(message_context, self.singular)
        else:
            text = translations.gettext(self.singular)
        return text, self.singular_vars

    def format_message(
        self,
        context: Context,
        message_text: str,
        message_vars: Dict[str, Any],
    ) -> str:
        """Return the message string formatted with the given message variables."""
        if context.env.autoescape:
            message_text = Markup(message_text)

        with context.extend(namespace=message_vars):
            _vars = {
                k: to_liquid_string(context.resolve(k), context.env.autoescape)
                for k in self.re_vars.findall(message_text)
            }

        return message_text % _vars

    def children(self) -> List[ChildNode]:
        children = [
            ChildNode(
                linenum=self.tok.linenum,
                node=self.singular_block,
                block_scope=list(self.args),
            )
        ]

        if self.plural:
            children.append(
                ChildNode(
                    linenum=self.plural.block.tok.linenum,
                    node=self.plural.block,
                    block_scope=list(self.args),
                )
            )

        children.extend(
            [
                ChildNode(linenum=self.tok.linenum, expression=expr)
                for expr in self.args.values()
            ],
        )

        return children

    def messages(self) -> Iterable[MessageText]:
        if not self.singular:
            return ()

        if self.plural:
            funcname = "ngettext"
            message: Tuple[str, ...] = (self.singular, self.plural.text)
        else:
            funcname = "gettext"
            message = (self.singular,)

        message_context = self.args.get(self.message_context_var)
        if isinstance(message_context, StringLiteral):
            funcname = "pgettext" if len(message) == 1 else "npgettext"
            return (
                MessageText(
                    lineno=self.tok.linenum,
                    funcname=funcname,
                    message=((message_context.value, "c"),) + message,
                ),
            )

        return (
            MessageText(
                lineno=self.tok.linenum,
                funcname=funcname,
                message=message,
            ),
        )
