
from __future__ import absolute_import

import datetime

################################################################################
def now():
    now = datetime.datetime.utcnow().replace(microsecond=0)
    now = now.isoformat("_").replace(":", "_")
    return now

