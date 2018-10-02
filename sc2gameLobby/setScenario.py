
"""PURPOSE: launch the mini-editor to create custom p setups"""

import glob
import os
import stat
import subprocess
import time

#from s2clientprotocol.raw_pb2 import ActionRawCameraMove
from s2clientprotocol.sc2api_pb2 import Action, RequestAction

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
def initScenario(controller, scenario, thisPlayerID, debug=False):
    """once in the in_game state, use the controller to set up the scenario"""
    ############################################################################
    def createUnitsWithTags(unitList, existingUnits={}, maxTries=25):
        """create each unit of unitList in game, identified by their tag"""
        createCmds = debugCmds.create(*unitList)
        controller.debug(*createCmds) # send create cmd via controller
        triesRemaining = maxTries
        getGameState = controller.observe # function that observes what's changed since the prior gameloop(s)
        numNeededNewUnits = len(unitList)
        newUnits = {}
        while len(newUnits) < numNeededNewUnits and triesRemaining > 0: # wait until new units are created
            units = getGameState().observation.raw_data.units
            for i, unit in enumerate(unitList): # match new unit tags with their originating units
                if unit.tag: continue # already found a matching tag for this unit
                for liveUnit in units: # identify new units and their tags
                    if liveUnit.unit_type != unit.code:     continue # can't match a unit of a different type
                    if liveUnit.owner     != unit.owner:    continue # can't match units with different owners
                    if liveUnit.tag       in existingUnits: continue # don't match against previously existing or new units
                    unit.tag = liveUnit.tag # found a match; sync tags + decalre this unit matched
                    existingUnits[unit.tag] = liveUnit # remember this association between unit and its properties
                    newUnits[unit.tag] = unit # distinguish the new units from the existing units
                    break # once a match is made, stop searching
                #if not unit.tag:  print("%02d.  missing: %s"%(maxTries-triesRemaining, unit))
            triesRemaining -= 1
        return newUnits
    ############################################################################
    def detectCurrentUnits(**filters):
        """identify all units currently visible by the player"""
        detectedUnits = {}
        getGameState = controller.observe # function that observes what's changed since the prior gameloop(s)
        while True:
            obs = getGameState()
            if obs.observation.game_loop <= 1: continue
            foundNewUnit = False
            for u in obs.observation.raw_data.units: # identify existing units (requieres no fog to be disabled?)
                if u.tag in detectedUnits: continue
                foundNewUnit = True
                detectedUnits[u.tag] = u
            if foundNewUnit: continue # ensure that two consecutive gameloops have identical units
            if detectedUnits: break # wait until units are found in the raw observations
        if filters:  return filterUnits(detectedUnits, **filters)
        else:        return detectedUnits
    ############################################################################
    def filterUnits(unitDict, noNeutral=False, ownedOnly=False):
        """select the desired types of units from unitDict"""
        ########################################################################
        def allow(unit):
            if noNeutral:
                if unit.alliance == c.NEUTRAL:              return False # ignore neutral units visible via snapshot to start the game
                if unit.mineral_contents:                   return False # don't include mineral nodes
                if unit.vespene_contents:                   return False # don't include vespene nodes
            if ownedOnly and unit.owner != thisPlayerID:    return False
            return True
        ########################################################################
        if not (noNeutral or ownedOnly): return unitDict # must select filters to get something different
        return {unit.tag : unit for unit in unitDict.values() if allow(unit)}
    ############################################################################
    def removeUnitsByKey(originalUnits=None, keepTags=[], **filters):
        """remove all detected units"""
        if originalUnits:
            units = filterUnits(originalUnits, **filters) # potentially filter an existing unit list
        else:
            originalUnits = detectCurrentUnits(**filters) # query currently existing units and filter appropriately
            units = originalUnits
        rmTags = list(units.keys())
        for keeper in keepTags:
            try:    rmTags.remove(keeper)
            except: pass
        return removeUnitsByTag(*rmTags, knownUnits=originalUnits)
    ############################################################################
    def removeUnitsByTag(*rmUnitTags, knownUnits={}):
        """remove specific units"""
        for rmTag in rmUnitTags:
            try:    del knownUnits[rmTag]
            except:
                if not knownUnits: break # already removed all monitored units
        if rmUnitTags:
            rmCmd = debugCmds.remove(*rmUnitTags) # create command to remove existing units
            controller.debug(rmCmd) # send remove cmd to remove existing units
        return knownUnits
    ############################################################################
    def wait(delay, msg):
        """control timing and messaging around delayed timing"""
        if debug: print(msg)
        while True:
            time.sleep(1)
            delay -= 1
            if delay > 0:
                if debug: print("%d..."%delay)
                continue
            break
    ############################################################################
    knownUnits = detectCurrentUnits(noNeutral=True) # all initial units, including misc units
    for pIdx, p in scenario.players.items():
        baseUnits = scenario.newBaseUnits(pIdx)
        newUs = createUnitsWithTags(p.baseUnits, existingUnits=knownUnits)
    wait(2, "delay before default unit deletion; %d remain"%len(newUs))
    if scenario.units: # remove initial units, but only if custom units are specified
        rmTags = []
        keepUnits = {19, 60, 95, 137} # supply depot, pylon, nydus network and burrowed creep tumor
        for unit in knownUnits.values():
            if unit.unit_type in keepUnits: continue # don't remove the main building
            rmTags.append(unit.tag) # collect all tags to remove them in a single command, all at once
        removeUnitsByTag(*rmTags, knownUnits=knownUnits) # skip 'knownUnits' option since initial units has already excluded rmTags
        wait(1, "idle for unit kills (keep %d)"%len(knownUnits))
        removeUnitsByKey(keepTags=knownUnits.keys(), noNeutral=True) # attempt again because zerg building deaths produce broodlings
    if debug:  print("%d remaining initial, known units"%len(knownUnits))
    initialUnits = dict(knownUnits)
    if thisPlayerID == 1: # this is the host (enable cheats for all players)
        controller.debug(debugCmds.disableAllCosts(), # enable cheats
                         debugCmds.allowEnemyControl(),
                         debugCmds.fastProduction())
    wait(0.5, "delay before creation") # wait before sending more commands
    actionLists = []
    nonActionLists = []
    newU = {}
    for playerID, upgrades in scenario.upgrades.items(): # set upgrades when appropriately specified in the scenario
        if not upgrades: continue
        reqs = scenario.players[playerID].upgradeReqs
        producingUnits = reqs.keys()
        if playerID == thisPlayerID:
            if debug: print("preparing %d upgrades for player #%d"%(len(upgrades), playerID))
            newU = createUnitsWithTags(producingUnits, existingUnits=knownUnits) # new units are created with in-game tags
        for unit, toDoActions in reqs.items():
            for i, ability in enumerate(toDoActions): # convert ability into requisite upgrade protocol action
                while len(actionLists) <= i:
                    actionLists.append([])
                    nonActionLists.append([])
                action = Action()
                uCmd = action.action_raw.unit_command
                uCmd.unit_tags.append(unit.tag)
                uCmd.queue_command = True
                uCmd.ability_id, ignoreTargetType = ability.getGameCmd() # upgrade abilities are targetless; therefore ignore target type of the action
                if playerID == thisPlayerID:    actionLists[i].append(action)
                else:                        nonActionLists[i].append(action)
    for i, (al, nal) in enumerate(zip(actionLists, nonActionLists)): # units that perform subsequent research commands must issue them consecutively
        if debug:  print("upgrade action list #%d commands: %d"%(i+1, len(al)))
        if al:  controller.actions(RequestAction(actions=al))
        elif not nal: continue # no player has any upgrade actions to perform for this tech level
        if   i == 0:  wait(6, "wait for all player's level 1 upgrades")
        elif i == 1:  wait(7, "wait for all player's level 2 upgrades")
        elif i == 2:  wait(8, "wait for all player's level 3 upgrades")
    if thisPlayerID == 1: # this is the host (disable cheats for all players)
        controller.debug(debugCmds.disableAllCosts(), # disable cheats
                         debugCmds.allowEnemyControl(),
                         debugCmds.fastProduction())
    wait(0.5, "wait to disable cheats before proceeding")
    if thisPlayerID == 1:
        removeUnitsByKey(keepTags=initialUnits, noNeutral=True) # remove tech researching units (and any other unit the player happened to create during research time
        wait(1.0, "idle for unit kills")
        knownUnits = removeUnitsByKey(keepTags=initialUnits, noNeutral=True) # attempt again in case zerg units produced broodlings
    cameraMv = Action()
    playerLoc = scenario.players[thisPlayerID].loc # set camera location to player's location
    playerLoc.assignIntoInt(cameraMv.action_raw.camera_move.center_world_space)
    controller.actions(RequestAction(actions=[cameraMv]))
    if debug: print("repositioned camera")
    scenarioUnits = {}
    for p in scenario.players.values(): # create the new scenario units only (not base units)
        newUnits = createUnitsWithTags(p.units, existingUnits=knownUnits)
        scenarioUnits.update(newUnits)
    modifyCmds = debugCmds.modify(*scenarioUnits.values()) # create command to set properties of in-game units
    controller.debug(*modifyCmds) # send modify cmd via controller
    wait(0.1, "allow modifications to finish")
    controller.debug(debugCmds.revealMap()) # reenable fog of war
    if debug:  print("scenario setup is finished")

