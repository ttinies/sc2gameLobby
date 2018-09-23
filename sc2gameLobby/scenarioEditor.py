
"""PURPOSE: launch the mini-editor to create custom p setups"""

import glob
import os
import stat
import subprocess

from sc2gameLobby import gameConstants as c
from sc2gameLobby.gameConfig import Config

# windows 10
banksDir = "C:\\Users\\jared\\Documents\\StarCraft II\\Banks"
availableBankNames = glob.glob(os.path.join(banksDir, "*"))
editorCmd = "%s -run %s -testMod %s -displayMode 1"
#EXAMPLE:
#C:\\StarCraft II\\Support64>SC2Switcher_x64.exe -run "Ladder\\CatalystLE.SC2Map" -testMod "C:\\Users\\TheWisp\\Documents\\PlayGround.SC2Mod"

################################################################################
def launchEditor(mapObj):
    """
    PURPOSE: launch the editor using a specific map object
    INPUT:   mapObj (sc2maptool.mapRecord.MapRecord)
    """
    cfg = Config()
    if cfg.is64bit: selectedArchitecture = c.SUPPORT_64_BIT_TERMS
    else:           selectedArchitecture = c.SUPPORT_32_BIT_TERMS
    fullAppPath = os.path.join(
        cfg.installedApp.data_dir,
        c.FOLDER_APP_SUPPORT%(selectedArchitecture[0]))
    appCmd = c.FILE_EDITOR_APP%(selectedArchitecture[1])
    fullAppFile = os.path.join(fullAppPath, appCmd)
    os.chmod(fullAppFile, stat.S_IRUSR|stat.S_IRGRP|stat.S_IROTH|stat.S_IXUSR|\
                          stat.S_IRUSR|stat.S_IWUSR|stat.S_IWGRP|stat.S_IXGRP) # switcher file must be executable
    finalCmd = editorCmd%(appCmd, mapObj.path, c.FILE_EDITOR_MOD)
    cwd = os.getcwd()
    os.chdir(fullAppPath)
    os.system(finalCmd)
    os.chdir(cwd) # restore back to original directory

