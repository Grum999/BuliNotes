import sys
import os.path

from .pktk import (PkTk, EInvalidType, EInvalidValue, EInvalidStatus)

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# now, pktk modules can be imported as:
# import pktk.modules.xxxxx
# import pktk.widgets.xxxxx
