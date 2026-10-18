# UC-004-REVEAL-AND-SCOREBOARD

## Intent

Reveal each photo's uploader, accumulate correct guesses across rounds, and let
the host end the game with a private-to-game-state-until-final ranked scoreboard
or start another game with the same players and zero scores.

## Actors

- Host: advances reveals, returns to the lobby, ends the game, or starts another
  game.
- Player: views the final scoreboard with their own rank and points.
- Reader: reads game state and the scoreboard.

## Preconditions

- The game exists and has completed at least one photo reveal in the current
  round.
- The host has the game's host token for host actions.
- Guesses and photo uploaders are available for completed rounds.

## Flow

1. After each photo's reveal, the host advances to the next photo when one
   remains.
2. After the last photo's reveal, the host either returns the game to `lobby`
   for the next round, preserving accumulated scores, or ends the game.
3. For each completed photo, the system awards one point to each player whose
   guess names the photo's uploader. A photo's uploader receives no point for
   their own photo.
4. While the game is not in `scoreboard`, game state does not contain points or
   ranks.
5. When the host ends the game, the system sets the phase to `scoreboard` and
   calculates the total points over all rounds.
6. The scoreboard lists every player in descending points order. Equal points
   share a rank, and the next rank skips accordingly (10, 7, 7, 3 ranks as 1,
   2, 2, 4).
7. Each player's scoreboard view includes their own rank and points and the full
   ranked list.
8. When the host chooses `Play again`, the system preserves the players,
   deletes all rounds, photos, and votes for the game, resets all scores to zero,
   and sets the phase to `lobby`.

## Errors

- Ending the game without a valid host token → 403.
- Playing again without a valid host token → 403.
- Requesting the scoreboard before the game is in `scoreboard` phase → 409.
- Unknown game → 404.

## Acceptance

Given a game in `reveal` after the last photo of a round
When the host returns to the lobby with a valid host token
Then the phase becomes `lobby` and scores remain accumulated for the next round

Given a completed photo and guesses from eligible players
When scoring is calculated
Then each correct guess earns one point, the uploader earns no point for their
own photo, and points accumulate across all completed rounds

Given a game before `scoreboard` phase
When any reader requests game state
Then points and ranks are not included

Given a game after the last photo of a round
When the host ends the game with a valid host token
Then the phase becomes `scoreboard` and the full ranked scoreboard is available

Given scoreboard points 10, 7, 7, and 3
When ranks are assigned
Then the ranks are 1, 2, 2, and 4

Given a game in `scoreboard` phase
When a player reads the scoreboard
Then the response includes that player's own rank and points and the full list
of players sorted highest points first

Given a game in `scoreboard` phase
When the host chooses `Play again` with a valid host token
Then the same players remain, all rounds, photos, and votes are deleted, all
scores are zero, and the phase becomes `lobby`

Given an invalid host token, an early scoreboard request, or an unknown game
When the related action is requested
Then the system returns 403, 409, or 404 respectively and does not perform the
requested state change

## Tests

- Unit: each correct eligible guess adds one point and an uploader receives no
  point for their own photo.
- Unit: points accumulate over multiple completed rounds and are hidden outside
  `scoreboard`.
- Unit: scoreboard sorting and competition ranking produce 1, 2, 2, 4 for
  points 10, 7, 7, 3.
- Unit: play-again reset preserves players and removes rounds, photos, votes,
  and scores.
- Integration: host returns to lobby after the last reveal while preserving
  scores.
- Integration: ending the game with a valid host token enters `scoreboard`.
- Integration: scoreboard request before `scoreboard` returns 409.
- Integration: scoreboard returns each player's rank and points plus the full
  sorted list.
- Integration: missing or wrong host tokens for ending or playing again return
  403.
- Integration: unknown game returns 404.
- Integration: play again resets the game to `lobby` with the same players and
  no rounds, photos, or votes.
- E2E: host reveals a round, ends the game, players see the ranked scoreboard,
  and the host starts another game with the same players at zero points.
