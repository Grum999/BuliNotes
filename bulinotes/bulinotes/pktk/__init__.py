import sys
import os.path

from .pktk import (PkTk, EInvalidType, EInvalidValue, EInvalidStatus)

pluginsPath=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if not pluginsPath in sys.path:
    # now, pktk modules for plugin <plugin> can be imported as:
    # import <plugin>.pktk.modules.xxxxx
    # import <plugin>.pktk.widgets.xxxxx
    sys.path.append(pluginsPath)

