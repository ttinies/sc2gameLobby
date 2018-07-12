# sc2gameLobby Python Usage

This document provides instruction how to (easy mode!) launch a desired Starcraft 2 match using a ladder that allows
play between both humans and AI / bots as a human or AI / bot player.

Instructions for non-python AI / bots are detailed separate [here](https://github.com/ttinies/sc2gameLobby/blob/master/USAGE_NON_PYTHON.md).

## Setup a Player

This player name is created locally.  When a new match request is sent to a ladder server using this player, if the
ladder server doesn't know this player already and accepts new players, the player is automatically created on the
ladder server as well.  If you're trying to create a player with a name already owned by another player, your match
request will be rejected.

1. Define ( [instructions](https://github.com/ttinies/sc2gameLobby/blob/master/USAGE_PYTHON.md) ) or select an
existing player.
	
**NOTES**
* If you want to play as a human yourself, be sure use a player where the type is set as `human`.
* If selecting a AI/bot player, the initialization command must provide a callback function that initializes your code
as you deem necessary in a list.  You may elect to return additional objects in this list which the sc2gameLobby
otherwise ignores, except to ensure they are preserved throughout the duration of the match.
* In realtime mode, it is possible to skip gameloop values and also possible to receive multiple copies of the
same observation, depending on how busy the Starcraft 2 game client is, latency associated with data transfer, etc. 


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

