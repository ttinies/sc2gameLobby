# sc2gameLobby Python Usage

This document provides instruction how to (easy mode!) launch a desired Starcraft 2 match using a ladder that allows
play between both humans and AI / bots as a human or AI / bot player.

Instructions for non-python AI / bots are detailed separate [here](https://github.com/ttinies/sc2gameLobby/blob/master/USAGE_NON_PYTHON.md).

## Setup a Player

This player name is created locally.  When a new match request is sent to a ladder server using this player, if the
ladder server doesn't know this player already and accepts new players, the player is automatically created on the
ladder server as well.  If you're trying to create a player with a name already owned by another player, your match
request will be rejected.

1. Define a player ([instructions](asdf)).
	
* If you want to play as a human yourself, be sure the type is set as `human`.
* If you're using code to understand data and make decisions, set the type as `bot`.
* If your code uses machine learning in some form to make its decisions, set the type as `ai`.

If you have a `bot` or `ai` type player, you must also specify the `initCmd` parameter.  The format for this value is
`<your_package_name>` followed by each additional package/module/attribute needed to access your initializing function.
First, your package will be imported.  Then each subsequent accessor is accessed until the presumed initializtion
routine can be invoked.  The initialization routine is called without any parameters.  The return value from this
function (callable) must be a list (an indexable iterable).  The first value (index 0) in this list must be a callback
function.  Each time a game state observation is received from the connected Starcraft 2 client, your callback function
is invoked and the observation is passed as a parameter.  Any additional indexes in the returned list can contain python
objects of any kind that you wish to persist over the course of the game. Additional indexes are optional and subject to
your own implementation.

> `initCmd` format EXAMPLE: "amazingBot.source.initFunction"

In this example, your bot is defined in the `amazingBot` package (which must be available in your environment).  It's 
submodule `source` is accessed and ultimately your `initFunction` is called.  The return value from `initFunction` must
be a list whose first index is a callback function. The callback function is invoked each time a new observation is
received.

## Play a Ladder Match

The command issued creates a configuration object which is sent to the ladder server as a new match request.  The ladder
server matches opponents in the game, determines a valid map and other match details to be supplied back to each player.
Only official Ladder or Tournament maps for the given game mode (i.e. 1v1) are used.  Because humans can play on this
ladder, each match is played with `realtime=True`.  The sc2gameLobby then automatically launches the Starcraft 2 client
using the configuration provided by ladder server to connect to other players and play the match.

2.  Launch `python sc2gameLobby` with the desired options.

> EXAMPLE: `python --nogui --player=<your_player_name>`

This example launches a match request as the specified player.  A very basic, nearly empty observation is obtained from
the client, so this works well for a human player.

> EXAMPLE: `python --nogui --raw --score --player=<your_player_name>`

The example launches a match request as the specified player.  It also specifies that `raw` and `score` information is
supplied in the observation data.  Presumably the specified player will use that

## Play a Custom Game

When specifying an option that creates a custom game, the results of the match aren't applied to the ladder ratings.

##### Play Against Specific Opponent(s)

Ensure you are matched only against this opponent, if available.
> `--opponents=<player_name_1>`

##### Play on a Specific Map

The map you play on must be this specific map.

> `--map=<name_of_desired_map>`

