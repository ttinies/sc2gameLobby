
import sys

import sc2gameLobby

from sc2gameLobby import cli

def test_import():
    assert bool(sc2gameLobby)
    

#def test_cli():
#    sys.argv = sys.argv[:1] + ["--search=defaulthuman"]
#    cli.main() # good request
#    sys.argv = sys.argv[:1] + ["--search=playerDoesNotExist4235nxprdjhqwhmdfxu"]
#    cli.main() # bad request
#    #sys.argv = sys.argv[:1] + ["--nogui"]
#    #cli.main() # NYI -- requires auto-dependency installation
#    sys.argv = sys.argv[:1] + ["--add"]
#    cli.main()
#    sys.argv = sys.argv[:1] + ["--update"]
#    cli.main()
#    sys.argv = sys.argv[:1] + ["--versions"]
#    cli.main()
#    sys.argv = sys.argv[:1] + ["--windowed", "--raw"]
#    cli.main() # launch GUI attempt, but error
#    sys.argv = sys.argv[:1] # restore sys.argv to no-arg state


#def test_cli_error1():
#    """test an invalid/offline server configuration"""
#    sys.argv = sys.argv[:1] + ["--ladder=testInvalid"]
#    cli.main()


#def test_cli_error2():
#    """test an invalid/offline server configuration"""
#    sys.argv = sys.argv[:1] + ["--ladder=testInvalid"]
#    cli.main()
