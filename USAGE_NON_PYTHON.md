
# sc2gameLobby Usage for non-python Applications

The document only applies to AI developers who have written their AI bots in a language other than python.  The following
instructions detail how such a developer would enable their bot to work with this lobby + ladder framework.

#### How to set up your AI or bot

1. Create a player definition ([instructions](asdf)).
	* The field `initCmd` is where you submit the system command that will execute your bot appropriately.
	* If your application consumes the raw port values on the command line, specify this value as `__PORT__` in the `initCmd` string.  This `__PORT__` value will be replaced with the actual port values as comma-separated integers without whitespace.
2.  Launch `python sc2gameLobby` with the desired options.
	* it is important that you specify the data you need in your observations.  See `--help` for more info as to what the `s2clientprotocol` provides for bot consumption.

## Operations That Are Handled For You by sc2gameLobby

#### Configuration Definition

To request a new match or send match results, sending the game configuration as a json object in the payload is required.  That info in the payload is used by the server to understand the type of game you are creating and how to create a valid game such that all players can connect to each other.  If this payload is invalid, your request will be rejected and no match will be made for you.

By default you the python `Config` functionality (in [gameConfig.py](https://github.com/ttinies/sc2gameLobby/blob/master/gameConfig.py)). You can replace this functionality with your own newMatch request, but its format to the server ultimately must match that defined [gameConfig.py](https://github.com/ttinies/sc2gameLobby/blob/master/gameConfig.py)).  It's content must be complete with at least as much the `Config` class definition.

## Operations you AI / Bot Must Perform

#### Recommended: upload post-match results and replay data to the ladder server

Because sc2gameLobby allows remote play, this means that some issues of network play (e.g. disconnects) require redundancy to still adequately understand what match result events transpired.  The solution sc2gameLobby uses is to have all players report the results and match data following the end of the match. The ladder server uses all of these reported match results and actual match data (replay data) to diagnose what actually happened.

It is highly recommended recommended to upload post-match results and data to the server ladder.  That said, it is not technically required (initial development on a bot may not care about match results).  **However**, if your non-python bot does not upload post-match results, you run the risk that one or more of these bad events occur:
1. You are trusting that your opponent uploads accurate results.  If they are malicious about their reported results, the ladder server is unable to detect their malicious actions unless your results offer a counter narrative.
2. It is possible that your opponent may also not report the match results at all.  If this occurs, your match may be treated as if it never launched in the first place.  The win/loss result may be invalidated.
3. It is somewhat more likely to encounter a result diagnosis problem on the ladder server without complete results.

Once your bot reaches a certain maturity level that the results of the match are important, it is expected that match results are reported.

If implementing your own routine to upload match results, consider referencing [connectToServer.py](https://github.com/ttinies/sc2gameLobby/blob/master/connectToServer.py) function
`reportMatchCompletion()` for an example of what's needed.  The payload sent to the ladder server is formatted as follows:

* json list comprising the following elements:
	1. match configuration as a python dictionary (later represented in json string format).
	2. match results where keys are the players in the match and the values are match result codes defined in [sc2common.constants](https://github.com/ttinies/sc2common/blob/master/constants.py) (the keywords contain a `RESULT_` prefix).
    3. A string representation of base64 binary data for the replay as obtained by the Starcraft 2 client (i.e. via sc2protocol `RequestSaveReplay` request).

FYI: the python version of sc2gameLobby handles all post-match reporting automatically.
