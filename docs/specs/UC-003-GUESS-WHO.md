# UC-003-GUESS-WHO

## Intent

Let players guess who took each photo and let the host control the voting and
reveal flow.

## Actors

- Player: a member of the game who is not the current photo's uploader.
- Host: the game's owner, who drives the voting and reveal phases.
- Reader: anyone who reads game state.

## Preconditions

- A game exists with at least one player and one photo in the current round.
- The game phase is `voting`.
- The current photo is displayed in the fixed random order set when uploads
  closed (see UC-002).

## Flow

1. A player who is not the current photo's uploader submits one guess naming
   another player of the same game as the photographer.
2. System validates that the guessed player belongs to the same game.
3. System stores the guess as that voter's latest guess for the current photo.
4. A player may submit a new guess while voting is open; the system keeps only
   the latest guess.
5. The host may read the vote progress, shown as the count of eligible players
   who have voted (e.g. "4 of 7 voted"), without seeing individual guesses.
6. Voting closes when the host closes it, or automatically when every eligible
   player has voted.
7. When voting closes the system sets the game phase to `reveal` and exposes
   the current photo's uploader.
8. The host advances from `reveal` to the next photo, returning the game to
   `voting`.
9. After the last photo the host returns the game to the lobby for the next
   round or ends the game (see UC-004).

## Errors

- Not in `voting` phase → 409.
- Voter is the current photo's uploader → 403 with message
  `This one's yours. Keep a straight face.`
- Guessed player is not in this game → 422.
- Unknown game, photo or player → 404.
- Missing or wrong host token for host actions → 403.

## Acceptance

Given a game in `voting` phase with a photo
When an eligible player guesses another player of the same game
Then the guess is recorded and may later be changed

Given an eligible player who has already guessed
When the same player submits a different guess
Then only the latest guess is kept

Given the host during voting
When they request vote progress
Then they receive the count and total of eligible voters, not individual guesses

Given a game in `voting` phase where all eligible players have guessed
When the last eligible vote is recorded
Then the phase becomes `reveal` and the uploader is shown

Given a game in `voting` phase with pending votes
When the host closes voting
Then the phase becomes `reveal` and the uploader is shown

Given a game in `reveal` phase with more photos remaining
When the host advances
Then the phase becomes `voting` for the next photo

Given a game in `reveal` phase after the last photo
When the host returns to lobby
Then the game phase becomes `lobby`

## Tests

- Unit: storing a guess keeps only the latest guess per eligible voter.
- Unit: auto-close triggers when the last eligible player votes.
- Unit: vote progress returns voted count and eligible total without leaking
  individual guesses.
- Integration: submit guess returns 403 when voter is the uploader.
- Integration: submit guess returns 422 when guessed player is not in the game.
- Integration: submit guess returns 409 when not in voting phase.
- Integration: submit guess returns 404 for unknown game, photo or player.
- Integration: host can read vote progress during voting.
- Integration: host can close voting and reveal the uploader.
- Integration: host can advance to the next photo.
- Integration: missing or wrong host token on host actions returns 403.
- E2E: players vote, host sees progress, reveal shows uploader, host advances
  through all photos.
