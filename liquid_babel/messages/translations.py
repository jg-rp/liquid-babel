"""Translation related objects used by filters, tags and extraction functions."""
from abc import ABC
from abc import abstractmethod

from typing import Any
from typing import Iterable
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Tuple
from typing import Union

from typing_extensions import Protocol

from liquid import escape
from liquid import Markup

try:
    from liquid import soft_str  # type: ignore
except ImportError:  # pragma: no cover
    soft_str = str  # pylint: disable=invalid-name

from liquid.expression import Expression
from liquid.expression import Filter

DEFAULT_KEYWORDS = {
    "t": None,
    "trans": None,
    "translate": None,
    "gettext": None,
    "ngettext": (1, 2),
    "pgettext": ((1, "c"), 2),
    "npgettext": ((1, "c"), 2, 3),
}

DEFAULT_COMMENT_TAGS = [
    "Translators:",
]


class Translations(Protocol):
    """The object expected to be available in a render context for
    translating message text.

    Could be a `GNUTranslations` instance from the `gettext` module,
    a Babel `Translations` object, or any object implementing `gettext`,
    `ngettext`, `pgettext` and `npgettext` methods.
    """

    def gettext(self, message: str) -> str:
        """Lookup the message in the catalog."""

    def ngettext(self, singular: str, plural: str, n: int) -> str:
        """Do plural-forms message lookup."""

    def pgettext(self, context: str, message: str) -> str:
        """Lookup the context and message in the catalog."""

    def npgettext(self, context: str, singular: str, plural: str, n: int) -> str:
        """Do plural-forms context and message lookup."""


MESSAGES = Union[
    str,
    Tuple[str, ...],
    Tuple[Tuple[str, str], str],
    Tuple[Tuple[str, str], str, str],
]


class MessageTuple(NamedTuple):
    """The tuple expected to be returned from babel extraction methods."""

    lineno: int
    funcname: str
    message: MESSAGES
    comments: List[str]


class MessageText(NamedTuple):
    """Partial message tuple returned from translatable tags."""

    lineno: int
    funcname: str
    message: MESSAGES


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


def to_liquid_string(val: Any, autoescape: bool) -> str:
    """Return a Liquid string representation of the given value."""
    if isinstance(val, str) or (autoescape and hasattr(val, "__html__")):
        pass
    elif isinstance(val, bool):
        val = str(val).lower()
    elif val is None:
        val = ""
    elif isinstance(val, list):
        if autoescape:
            val = Markup("").join(soft_str(itm) for itm in val)
        else:
            val = "".join(soft_str(itm) for itm in val)
    elif isinstance(val, range):
        val = f"{val.start}..{val.stop - 1}"
    else:
        val = str(val)

    if autoescape:
        val = escape(val)

    assert isinstance(val, str)
    return val
