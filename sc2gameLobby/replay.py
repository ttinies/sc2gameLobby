
from __future__ import absolute_import
from __future__ import division       # python 2/3 compatibility
from __future__ import print_function # python 2/3 compatibility

import os

from sc2gameLobby import dateFormat
from sc2gameLobby import gameConstants as c


################################################################################
def save(self, ver, replayData):
    """give acquired replay data, save it as data for later interpretation"""
    matchDir = os.path.abspath(os.sep.join(
        __file__.split(os.sep)[:-2] + [c.FOLDER_PLAYED_VIDEO, self.mapName]))
    if not os.path.isdir(matchDir): os.makedirs(matchDir)
    replayFile = "%s%s%s_%s.%s"%(matchDir, os.sep, ver.toFilename(), dateFormat.now(), c.SC2_FILE_REPLAY)
    with open(replayFile, "wb") as f:
        f.write(replayData)
    return replayFile

