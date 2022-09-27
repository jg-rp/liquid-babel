"""Extract localization messages from Liquid templates."""
import os
from pathlib import Path

from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import Optional
from typing import TextIO
from typing import Tuple
from typing import Union

from babel.messages import Catalog

from liquid import Environment
from liquid.ast import Node

from liquid.expression import Expression
from liquid.expression import FilteredExpression

from liquid.template import BoundTemplate
from liquid.token import TOKEN_TAG
from liquid.builtin.tags.comment_tag import CommentNode

from .translations import DEFAULT_COMMENT_TAGS
from .translations import DEFAULT_KEYWORDS
from .translations import MessageText
from .translations import MessageTuple
from .translations import TranslatableFilter
from .translations import TranslatableTag

SPEC = Union[
    Tuple[int, ...],
    Tuple[Tuple[int, str], int],
    Tuple[Tuple[int, str], int, int],
]


def extract_from_templates(
    *templates: BoundTemplate,
    keywords: Optional[Dict[str, Any]] = None,
    comment_tags: Optional[List[str]] = None,
    strip_comment_tags: bool = False,
) -> Catalog:
    """Extract messages from one or more templates.

    This function returns a single ``babel.messages.Catalog`` containing
    messages from all the given templates.

    :param templates: templates to extract messages from.
    :param keywords: a Babel compatible mapping of translatable "function"
        names to argument specs. The included translation filters and tag
        transform their messages into typical *gettext format, regardless
        of their names.
    param comment_tags: a list of translator tags to search for and
        include in extracted messages.
    param strip_comment_tags: if `True`, remove comment tags from collected
        message comments.
    """
    keywords = keywords or DEFAULT_KEYWORDS
    comment_tags = comment_tags or DEFAULT_COMMENT_TAGS
    catalog = Catalog()
    for template in templates:
        for lineno, funcname, messages, comments in extract_from_template(
            template, keywords, comment_tags
        ):
            # A partial reimplementation of Babel's messages.extract function.
            # See https://github.com/python-babel/babel/blob/master/babel/messages/extract.py#L262
            spec: SPEC = keywords[funcname] or (1,)
            if not isinstance(messages, (list, tuple)):
                messages = (messages,)
            if not messages:
                continue
            if len(spec) != len(messages):
                continue

            # Assumes context is the first item in the spec
            if isinstance(spec[0], tuple):
                # context aware message
                context = messages[spec[0][0] - 1][0]
                message = [messages[i - 1] for i in spec[1:]]
            else:
                context = None
                message = [messages[i - 1] for i in spec if isinstance(i, int)]

            if not message[0]:
                # Empty message
                continue

            if strip_comment_tags:
                comments = _strip_comment_tags(comments, comment_tags)

            # Use the template's path if it has one
            template_name = template.name
            if isinstance(template.path, Path):
                template_name = str(template.path.joinpath(template_name))
            elif isinstance(template.path, str):
                template_name = os.path.join(template.path, template_name)

            catalog.add(
                message[0] if len(message) == 1 else message,
                "",
                [(template_name, lineno)],
                auto_comments=comments,
                context=context,
            )

    return catalog


def extract_liquid(
    fileobj: TextIO,
    keywords: List[str],
    comment_tags: Optional[List[str]] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Iterator[MessageTuple]:
    """A babel compatible extraction method for Python Liquid templates.

    See https://babel.pocoo.org/en/latest/messages.html

    Keywords are the names of Liquid filters or tags operating on translatable
    strings. For a filter to contribute to message extraction, it must also
    appear as a child of a `FilteredExpression` and be a `TranslatableFilter`.
    Similarly, tags must produce a node that is a `TranslatableTag`.

    Where a Liquid comment contains a prefix in `comment_tags`, the comment
    will be attached to the translatable filter or tag immediately following
    the comment. Python Liquid's non-standard shorthand comments are not
    supported.

    Options are arguments passed to the `liquid.Template` constructor with the
    contents of `fileobj` as the template's source. Use `extract_from_template`
    to extract messages from an existing template bound to an existing
    environment.
    """
    # pylint: disable=import-outside-toplevel
    from liquid_babel.filters import register_translation_filters
    from liquid_babel.tags.translate import TranslateTag

    env = Environment(**options or {})
    register_translation_filters(env, replace=False)
    env.add_tag(TranslateTag)
    template = env.from_string(fileobj.read())
    return extract_from_template(
        template=template,
        keywords=keywords,
        comment_tags=comment_tags,
    )


def extract_from_template(
    template: BoundTemplate,
    keywords: Union[List[str], Dict[str, Any], None] = None,
    comment_tags: Optional[List[str]] = None,
) -> Iterator[MessageTuple]:
    """Extract translation messages from a Liquid template."""
    _comment_tags = comment_tags or DEFAULT_COMMENT_TAGS
    _comments: List[Tuple[int, str]] = []
    _keywords = keywords or DEFAULT_KEYWORDS

    def visit_expression(expr: Expression, lineno: int) -> Iterator[MessageTuple]:
        if isinstance(expr, FilteredExpression):
            for _lineno, funcname, message in _extract_from_filters(
                template.env,
                expr,
                lineno,
                _keywords,
            ):
                if _comments and _comments[-1][0] < lineno - 1:
                    _comments.clear()

                yield MessageTuple(
                    lineno=_lineno,
                    funcname=funcname,
                    message=message,
                    comments=[text for _, text in _comments],
                )
                _comments.clear()

        for expression in expr.children():
            yield from visit_expression(expression, lineno)

    def visit(node: Node) -> Iterator[MessageTuple]:
        token = node.token()
        if isinstance(node, CommentNode) and node.text is not None:
            comment_text = node.text.strip()
            for comment_tag in _comment_tags:
                if comment_text.startswith(comment_tag):
                    # Our multi-line comments are wrapped in a tag, so we're
                    # only ever going to have one comment text object to deal
                    # with.
                    _comments.clear()
                    _comments.append((node.tok.linenum, comment_text))
                    break
        elif (
            token.type == TOKEN_TAG
            and token.value in _keywords
            and isinstance(node, TranslatableTag)
        ):

            for lineno, funcname, message in node.messages():
                if _comments and _comments[-1][0] < lineno - 1:
                    _comments.clear()

                yield MessageTuple(
                    lineno=lineno,
                    funcname=funcname,
                    message=message,
                    comments=[text for _, text in _comments],
                )
                _comments.clear()

        for child in node.children():
            if child.expression:
                yield from visit_expression(child.expression, token.linenum)
            if child.node:
                yield from visit(child.node)

    for node in template.tree.statements:
        yield from visit(node)


def _extract_from_filters(
    environment: Environment,
    expression: FilteredExpression,
    lineno: int,
    keywords: Union[List[str], Dict[str, Any]],
) -> Iterator[MessageText]:
    if expression.filters:
        # Only the first in a chain of filters is extractable.
        _filter = expression.filters[0]
        filter_func = environment.filters.get(_filter.name)
        if _filter.name in keywords and isinstance(filter_func, TranslatableFilter):
            message = filter_func.message(expression.expression, _filter, lineno)  # type: ignore
            if message:
                yield message


def _strip_comment_tags(comments: List[str], tags: List[str]) -> List[str]:
    """Similar to Babel's messages.extract._strip_comment_tags."""

    def _strip(line: str) -> str:
        for tag in tags:
            if line.startswith(tag):
                return line[len(tag) :].strip()
        return line

    return [_strip(comment) for comment in comments]
