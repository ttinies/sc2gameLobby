
import multiprocessing # ensure that multiProcessing.Queue can be instantiated in a child process


################################################################################
def doNothing(observation):
    """simply ignore the observation
    default callaback unless specified otherwise.
    useful if a human is playing unaided
    """


################################################################################
class forwardObservation(object):
    """allow the observation getter to connect to the commander by forwarding observations"""
    ############################################################################
    def __init__(self, pushQueue):
        self.pushQ = pushQueue
    ############################################################################
    def __call__(self, observation):
        self.pushQ.put(observation)

