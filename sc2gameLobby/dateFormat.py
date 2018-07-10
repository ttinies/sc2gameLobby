
from __future__ import absolute_import
from __future__ import division       # python 2/3 compatibility
from __future__ import print_function # python 2/3 compatibility

import datetime

################################################################################
def now(givenTime=None):
    if givenTime:   usableTime = datetime.datetime.utcfromtimestamp(givenTime)
    else:           usableTime = datetime.datetime.utcnow()
    now = usableTime.replace(microsecond=0)
    now = now.isoformat("_").replace(":", "_")
    return now

