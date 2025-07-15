#backend/logistics/parsers/registry.py
from .brenger import BrengerParser
from .swdevries import SwdevriesParser
from .libero import LiberoParser
from .wuunder import WuunderParser
from .tadde import TaddeParser
from .magic_movers import MagicMoversParser

parser_registry = {
    "brenger": BrengerParser,
    "swdevries": SwdevriesParser,
    "libero": LiberoParser,
    "wuunder": WuunderParser,
    "tadde" : TaddeParser,
    "magic_movers" : MagicMoversParser,
}
