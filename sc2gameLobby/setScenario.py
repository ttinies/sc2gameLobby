
"""PURPOSE: launch the mini-editor to create custom p setups"""

import glob
import os
import stat
import subprocess

from sc2gameLobby import debugCmds
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


################################################################################
def initScenario(controller, scenario):
    """once in the in_game state, use the controller to set up the scenario"""
    knownUnits = []
    gl = 0
    getGameState = controller.observe # function that observes what's changed since the prior gameloop(s)
    scenarioUnits = list(scenario.units.values())
    while True:
        obs = getGameState()
        if obs.observation.game_loop <= 1: continue
        knownUnits = obs.observation.raw_data.units # identify existing units (requieres no fog to be disabled?)
        if knownUnits: break # wait until units are found in the raw observation
    createCmds = debugCmds.create(*scenarioUnits)
    controller.debug(*createCmds) # send create cmd via controller
    rmTags = []
    keepUnits = {18, 59, 86} # command center, nexus and hatchery
    for unit in list(knownUnits):
        if unit.alliance == c.NEUTRAL:  continue # ignore neutral units visible via snapshot to start the game
        if unit.mineral_contents:       continue # don't remove mineral nodes
        if unit.vespene_contents:       continue # don't remove vespene nodes
        if unit.unit_type in keepUnits: continue # don't remove the main building
        rmTags.append(unit.tag)
    if rmTags:
        rmCmd = debugCmds.remove(*rmTags) # create command to remove existing units
        controller.debug(rmCmd) # send remove cmd to remove existing units
    newUnits = {}
    triesRemaining = 15
    while len(newUnits) < len(scenarioUnits) and triesRemaining > 0: # wait until new units are created
        units = getGameState().observation.raw_data.units
        for i, unit in enumerate(scenarioUnits): # match new unit tags with their originating units
            if unit.tag: continue # already found a matching tag for this unit
            for liveUnit in units: # identify new units and their tags
                if liveUnit.unit_type != unit.code:  continue # can't match a unit of a different type
                if liveUnit.owner     != unit.owner: continue # can't match units with different owners
                if liveUnit.tag       in newUnits:   continue # don't match the same unit twice
                unit.tag = liveUnit.tag # found a match; sync tags + decalre this unit matched
                newUnits[unit.tag] = unit # remember this association between unit and its properties
                break # once a match is made, stop searching
            if not unit.tag:
                print("%02d.  missing: %s"%(15-triesRemaining, unit))
        triesRemaining -= 1
    for term in newUnits:
        print(term)
    modifyCmds = debugCmds.modify(*newUnits.values()) # create command to set properties of in-game units
    #controller.debug(*modifyCmds) # send modify cmd via controller
    print("announce scenario setup is finished")

