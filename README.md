[![Build Status](https://travis-ci.com/mikemhenry/sc2gameLobby.svg?branch=master)](https://travis-ci.com/mikemhenry/sc2gameLobby)
[![Coverage Status](https://coveralls.io/repos/github/mikemhenry/sc2gameLobby/badge.svg?branch=master)](https://coveralls.io/github/mikemhenry/sc2gameLobby?branch=master)

# Play Starcraft 2 on a ladder as a human or AI against other human AI

## About

The objective of this repository is enable casual Starcraft 2 players, AI developers and proficient coders to all create a player that competes against others in a Starcraft 2 match.  The strategy is to create an increasingly user-friendly interface so that most anybody can readily set up matches and play against

#### Rationale: Why Create this Repository?

There is an existing ladder for AI-only developers, [sc2ai.net](https://sc2ai.net/).  While that project is under active development as of July 6, 2018, its roadmap doesn't support several critical features which impedes developers' efforts (such as ours) to create AI that is publicly visible.  Here are several features which this ladder supports that sc2ai.net may not.

* Play on your own machine against others on their own machines.  You're no longer limited by some other person's machine who is sharing system resources with other players in the game.
* Support AI vs AI, AI vs human and human vs human play.
* AI developers aren't required to share their source code or any executable.
* Fast, user-friendly setup that non-programmers or programmers with lower proficiency in a specific language can set up.  No need to hunt + edit files by hand.

#### Brief Functional Overview

This sc2gameLobby package's primary functions are as follows:
1. Issue match requests such that other available players or static bots can be matched against you. When being matched against opponents, if no valid opponents are available for a match with you in the queue, you are automatically matched instead against other publicly available bot algorithms or Blizzard's built-in bots depending on your estimated proficiency.
2. Launch a Starcraft 2 client that will automatically manage the match along with other Starcraft 2 clients (as needed).  The match is played until its finished.
3. Each sc2gameLobby reports results back to the ladder. The ladder verifies each player's reported results against its own intimate knowledge of the match to accurately determine the proper match result and update the ladder accordingly.

Communication with the ladder server occurs via TCP connection with a django server available on the internet.  It is possible to communicate with [alternative ladders](https://github.com/ttinies/sc2ladderMgmt), but we've established this server form normal sc2gameLobby gameplay.

## Installation

#### System Requirements

* sc2gameLobby is proven using both Linux (using wine) and Windows.  While untested on OSX, because OSX is also widely tested using pysc2, sc2gameLobby is also expected to work without issue.  NOTE: Linux is not a platform officially supported by Blizzard for Starcraft 2, but it does work, both using headless and regular setups using full graphics.
* As a human, your own system must be able to support a Starcraft 2 client application (the window that actually plays the game).  Reference standard [Starcraft 2 game requirements](https://us.battle.net/support/en/article/27575) for details.
* As an AI, in addition to the requirements for human play,  as well as any other resources your AI may require.  If your AI architecture can run, it is allowed on this ladder.

#### Instructions

1. Install Starcraft 2 normally.  If you use an install destination path other than the default, ensure it's specified using an environment variable called SC2PATH.
2. Install any(?) version of [python](https://www.python.org/downloads/) that is compatible with your system.
3. Use conda **or** pip via instructions below to install sc2gameLobby.
> NOTE: you can also install this package via other means, but you may have to manage your environment to ensure all dependencies are available on your system.  If you're not familiar with these utilities, follow the installation instructions provided by their authors available on the internet.

##### Conda

From a command line, enter a standard [conda](https://conda.io/docs/user-guide/index.html) install command that's 
compatible with your system setup.  Be sure you're targeting the intended environment!

> `EXAMPLE: conda install sc2gameLobby -n <your development environment name>`

##### Pip

From a command line, enter a standard [pip](http://pip.pypa.io/en/stable/user_guide/) install command that's compatible 
with your system setup.

> `EXAMPLE: pip install sc2gameLobby`

#### Dependencies

This sc2gameLobby package is indended to run with python version > 3.6.  It may very well work with older versions, but 
no assurances are provided.

This sc2gameLobby package is dependent on the following additional packages.  If using the above installation methods, 
these will automatically be installed.

* Package [sc2common](https://github.com/ttinies/sc2common)       -- common definitions for all Starcraft 2 implementations.
* Package [sc2ladderMgmt](https://github.com/ttinies/sc2ladderMgmt) -- manage the compatible ladders.
* Package [sc2maptool](https://github.com/ttinies/sc2gameMapRepo) -- manage available Starcraft 2 maps.
* Package [sc2players](https://github.com/ttinies/sc2players) -- manage players locally that are available on the ladder.
* Package [pysc2](https://github.com/deepmind/pysc2) -- Deepmind's foray into Starcraft 2 machine learning.
* Package [s2clientprotocol](https://github.com/Blizzard/s2client-proto/tree/master/s2clientprotocol) -- Blizzard's official protocol that supports communication with a Starcraft 2 game client.
* Package [six](https://pypi.org/project/six/) -- python 2/3 compatibility

#### Verification of Valid Installation

If your setup is fully successful, the following test commands should work as follows:

test command: `python -m sc2gameLobby --help`

```
usage: __main__.py [-h] [--nogui] [--search PLAYERS] [--history] [-l] [-p]
...
PURPOSE: front-end interface to easily and reliably match against opponents
and run Starcraft2 opponents.
...
version: 0.7.0
```

test command: `> python -m sc2gameLobby --versions`

```
...
4.4.0
   base-version: 65895
      data-hash: BF41339C22AE2EDEBEEADC8C75028F7D
     fixed-hash:
          label: 4.4.0
    replay-hash:
        version: 65895
```

test command: `python -m sc2gameLobby --search mapexplorer`

```
<PlayerRecord mapexplorer ai>
           type : <PlayerDesigns ai>
     difficulty : None
        initCmd : sc2ai.agents.newExplorer
         rating : 0
        created : 2018-05-28
```

#### Troubleshooting

```
ERROR: A connection could not be made. <Ladder versentiedge> may not be available or you may not be connected to the internet.
```

This means that the ladder server instance you are attempting to communicate with could not be reached.  It may not be online or your connection to the internet may be compromised.

**<reserved for additional issues if/when such are reported>**

## Recommended Usage

Great, now you're set to rock ladder matches versus humans and AI opponents!  Refer to [python](https://github.com/ttinies/sc2gameLobby/blob/master/USAGE_PYTHON.md)-specific or [non python](https://github.com/ttinies/sc2gameLobby/blob/master/USAGE_NON_PYTHON.md)-specific usage documents.  Good luck!

## Further Development and Augmentation

#### Add New Features to the Code?

This is an open-use repository.  Feel free to fork and issue pull requests. Feature enhancements, especially for to-be-developed features, and bug fixes are especially appreciated.

###### Anticipated Useful, To-Be-Developed Features

* User-friendly GUI front end that abstracts the command-line utilities.
* Web browser integration to perform match requests.
* Publicly available web page statistics from data mining match results.
* Additional game modes beyond 1v1.
