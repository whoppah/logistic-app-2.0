#backend/logistics/tasks/registry.py
# logistics/tasks/registry.py

from .brenger import BrengerParser
from .swdevries import SwdevriesParser
from .libero import LiberoParser

parser_registry = {
    "brenger": BrengerParser,
    "swdevries": SwdevriesParser,
    "libero": LiberoParser,
}
