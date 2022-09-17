from liquid.ast import Node
from liquid.tag import Tag

from liquid_babel.messages.translations import TranslatableTag


class TranslateTag(Tag):
    pass


class TranslateNode(Node, TranslatableTag):
    pass
