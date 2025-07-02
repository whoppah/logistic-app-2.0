#backend/logistics/parsers/registry.py
from .brenger import BrengerParser
from .swdevries import SwdevriesParser
from .libero import LiberoParser
from .wuunder import WuunderParser

parser_registry = {
    "brenger": BrengerParser,
    "swdevries": SwdevriesParser,
    "libero": LiberoParser,
    "wuunder": WuunderParser,
}
