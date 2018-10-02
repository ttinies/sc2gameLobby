
from s2clientprotocol.common_pb2 import Point2D
from s2clientprotocol.debug_pb2 import DebugCommand
from s2clientprotocol.debug_pb2 import DebugCreateUnit
from s2clientprotocol.debug_pb2 import DebugKillUnit
from s2clientprotocol.debug_pb2 import DebugSetUnitValue


################################################################################
def create(*units):
    """create this unit within the game as specified"""
    ret = []
    for unit in units: # implemented using sc2simulator.ScenarioUnit
        x, y = unit.position[:2]
        pt = Point2D(x=x, y=y)
        unit.tag = 0 # forget any tag because a new unit will be created
        new = DebugCommand(create_unit=DebugCreateUnit(
            unit_type   = unit.code,
            owner       = unit.owner,
            pos         = pt,
            quantity    = 1,
        ))
        ret.append(new)
    return ret


################################################################################
def modify(*units):
    """set the unit defined by in-game tag with desired properties
    NOTE: all units must be owned by the same player or the command fails."""
    ret = []
    for unit in units: # add one command for each attribute
        for attr, idx in [("energy", 1), ("life", 2), ("shields", 3)]: # see debug_pb2.UnitValue for enum declaration
            newValue = getattr(unit, attr)
            if not newValue: continue # don't bother setting something that isn't necessary
            new = DebugCommand(unit_value=DebugSetUnitValue(
                value       = newValue,
                unit_value  = idx,
                unit_tag    = unit.tag))
            ret.append(new)
    return ret


################################################################################
def remove(*tags):
    """remove the in-game units specified by tags from the game"""
    return DebugCommand(kill_unit=DebugKillUnit(tag=tags))


################################################################################
def revealMap():            return setGameState(1)  # disable/enable fog of war
def allowEnemyControl():    return setGameState(2)  # gain ability to share control of enemy units
def disableFoodSupply():    return setGameState(3)  # all units no longer consume food/supply
def disableAllCosts():      return setGameState(4)  # all units and buildings are free to build (no mineral/vespene cost)
def giveAllResources():     return setGameState(5)  # grants 5000 mineral and vespene
def enableGodMode():        return setGameState(6)  # your units are invulnerable and one-hit kill enemies
def giveMineral():          return setGameState(7)  # grants 5000 mineral
def giveVespene():          return setGameState(8)  # grants 5000 vespene
def disableCooldown():      return setGameState(9)  # removes all ability cooldowns
def disableTechReqs():      return setGameState(10) # allows USE of all tech, but does not actually research the abilities
def advAllTechOneLevel():   return setGameState(11) # advances research of ALL techs one level including those which only have one level
def fastProduction():       return setGameState(12) # construction and research speed is greatly increased (but not instant)
def setGameState(enumVal):
    """reference lines 69-82 of this file:
    https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/debug.proto
    """
    return DebugCommand(game_state=int(enumVal))

