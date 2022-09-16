"""Extract localization messages from Liquid templates."""
from abc import ABC
from abc import abstractmethod

from typing import Any
from typing import Dict
from typing import Iterable
from typing import Iterator
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import TextIO
from typing import Tuple
from typing import Union

from liquid import Environment
from liquid import Template
from liquid.ast import Node

from liquid.expression import Expression
from liquid.expression import Filter
from liquid.expression import FilteredExpression

from liquid.template import BoundTemplate
from liquid.token import TOKEN_TAG
from liquid.builtin.tags.comment_tag import CommentNode


class MessageTuple(NamedTuple):
    """The tuple expected to be returned from babel extraction methods."""

    lineno: int
    funcname: str
    message: Union[str, Tuple[str, ...]]
    comments: List[str]


class MessageText(NamedTuple):
    """Partial message tuple returned from translatable tags."""

    lineno: int
    funcname: str
    message: Tuple[str, ...]


class TranslatableTag(ABC):  # pylint: disable=too-few-public-methods
    """Base class for translatable tags."""

    @abstractmethod
    def messages(self) -> Iterable[MessageText]:
        """Generate a sequence of translation messages."""


class TranslatableFilter(ABC):  # pylint: disable=too-few-public-methods
    """Base class for translatable filters."""

    @abstractmethod
    def message(
        self,
        left: Expression,
        _filter: Filter,
        lineno: int,
    ) -> Optional[MessageText]:
        """Generate a sequence of translation messages."""


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
    template = Template(fileobj.read(), **options or {})
    # TODO: register default translation filter funcs
    return extract_from_template(
        template=template,
        keywords=keywords,
        comment_tags=comment_tags,
    )


def extract_from_template(
    template: BoundTemplate,
    keywords: List[str],
    comment_tags: Optional[List[str]] = None,
) -> Iterator[MessageTuple]:
    """"""

    _comment_tags = comment_tags or []
    _comments: List[Tuple[int, str]] = []

    def visit_expression(expr: Expression, lineno: int) -> Iterator[MessageTuple]:
        if isinstance(expr, FilteredExpression):
            for _lineno, funcname, message in _extract_from_filters(
                template.env,
                expr.expression,
                expr.filters,
                lineno,
                keywords,
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
            and token.value in keywords
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
    expression: Expression,
    filters: List[Filter],
    lineno: int,
    keywords: List[str],
) -> Iterator[MessageText]:
    """"""
    for _filter in filters:
        filter_func = environment.filters.get(_filter.name)
        if _filter.name in keywords and isinstance(filter_func, TranslatableFilter):
            yield filter_func.message(expression, _filter, lineno)  # type: ignore
