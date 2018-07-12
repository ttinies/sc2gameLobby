
import sys

import sc2gameLobby


def test_cli():
    sys.argv = sys.argv[:1] + ["--search=defaulthuman"]
    sc2gameLobby.cli.main() # good request
    sys.argv = sys.argv[:1] + ["--search=playerDoesNotExist4235nxprdjhqwhmdfxu"]
    sc2gameLobby.cli.main() # bad request
    #sys.argv = sys.argv[:1] + ["--nogui"]
    #sc2gameLobby.cli.main() # NYI -- requires auto-dependency installation
    sys.argv = sys.argv[:1] + ["--add"]
    sc2gameLobby.cli.main()
    sys.argv = sys.argv[:1] + ["--update"]
    sc2gameLobby.cli.main()
    sys.argv = sys.argv[:1] + ["--versions"]
    sc2gameLobby.cli.main()
    sys.argv = sys.argv[:1] + ["--windowed", "--raw"]
    sc2gameLobby.cli.main() # launch GUI attempt, but error
    sys.argv = sys.argv[:1] # restore sys.argv to no-arg state


def test_cli_error1():
    """test an invalid/offline server configuration"""
    sys.argv = sys.argv[:1] + ["--ladder=testInvalid"]
    sc2gameLobby.cli.main()


def test_cli_error2():
    """test an invalid/offline server configuration"""
    sys.argv = sys.argv[:1] + ["--ladder=testInvalid"]
    sc2gameLobby.cli.main()
