from liquid.ast import Node
from liquid.tag import Tag

from liquid_babel.messages.extract import TranslatableTag


class TranslateTag(Tag):
    pass


class TranslateNode(Node, TranslatableTag):
    pass
