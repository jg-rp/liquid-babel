from abc import ABC
from abc import abstractmethod

from typing import Iterable
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Tuple
from typing import Union

from typing_extensions import Protocol

from liquid.expression import Expression
from liquid.expression import Filter


class Translations(Protocol):
    def gettext(self, message: str) -> str:
        ...

    def ngettext(self, singular: str, plural: str, n: int) -> str:
        ...

    def pgettext(self, context: str, message: str) -> str:
        ...

    def npgettext(self, context: str, singular: str, plural: str, n: int) -> str:
        ...


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
