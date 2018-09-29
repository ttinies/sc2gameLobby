
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
    """set the unit defined by in-game tag with desired properties"""
    ret = []
    for unit in units: # add one command for each attribute
        for attr, idx in [("energy", 1), ("life", 2), ("shields", 3)]: # see debug_pb2.UnitValue for enum declaration
            newValue = getattr(unit, attr)
            if not newValue: continue # don't bother setting something that isn't necessary
            if attr != "energy": continue
            new = DebugCommand(unit_value=DebugSetUnitValue(
                value       = 125.0,#newValue,
                unit_value  = idx,
                unit_tag    = unit.tag))
            if attr == "energy": print(new)
            ret.append(new)
    return ret


################################################################################
def remove(*tags):
    """remove the in-game units specified by tags from the game"""
    return DebugCommand(kill_unit=DebugKillUnit(tag=tags))

