"""Extract localization messages from Liquid templates."""
from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import TextIO


from liquid import Template
from liquid.template import BoundTemplate


class MessageTuple(NamedTuple):
    """The tuple expected to be returned from babel extraction methods."""

    lineno: int
    funcname: str
    message: str
    comments: List[str]


def extract_liquid(
    fileobj: TextIO,
    keywords: List[str],
    _: Optional[List[str]] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Iterator[MessageTuple]:
    """A babel compatible extraction method for Python Liquid templates.

    See https://babel.pocoo.org/en/latest/messages.html

    Keywords are the names of Liquid filters operating on translatable
    strings. Any Liquid.ast.Node class that defines a `messages` method
    will also be recognized as containing translatable strings.

    Comment tags are currently ignored as it is assumed that a translatable
    Liquid tag or filter knows how to find its own comments.

    Options are arguments passed to the liquid.Template constructor with
    the contents of `fileobj` as the template's source.

    Use `extract_from_template` to extract messages from an existing
    template bound to an existing environment.
    """
    template = Template(fileobj.read(), **options or {})
    return extract_from_template(template=template, keywords=keywords)


def extract_from_template(
    template: BoundTemplate,
    keywords: List[str],
) -> Iterator[MessageTuple]:
    """"""
    # TODO:
