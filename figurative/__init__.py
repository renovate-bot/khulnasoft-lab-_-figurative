import sys

if sys.version_info < (3, 7):
    print("Figurative requires Python 3.7 or higher.")
    sys.exit(-1)

from .utils import config, log
from .utils.log import set_verbosity
from .core.smtlib import issymbolic, istainted
from .ethereum.figurative import FigurativeEVM
from .core.plugin import Plugin
from .exceptions import FigurativeError

__all__ = [
    issymbolic.__name__,
    istainted.__name__,
    FigurativeEVM.__name__,
    set_verbosity.__name__,
    FigurativeError.__name__,
]
