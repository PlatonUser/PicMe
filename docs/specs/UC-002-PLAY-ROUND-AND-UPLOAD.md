# UC-002-PLAY-ROUND-AND-UPLOAD

## Intent

Let the host start a prompt round and let each player submit one photo before
the server-enforced deadline, preparing the photos for voting.

## Actors

- Host: chooses the prompt and upload duration, starts the round, and controls
  the upload deadline.
- Player: uploads or replaces one JPEG photo during the upload phase.
- Reader: reads game state; reads also enforce deadline-driven phase changes.

## Preconditions

- The game exists and is in `lobby` phase.
- The host has the game's host token.
- Players may be present; an upload round can close without any photos.
- Prompt categories and prompts are available from `docs/reference/prompts.ts`.

## Flow

1. The host selects a prompt source:
   - a chosen category;
   - `Shuffle`, which selects from all categories; or
   - a non-empty prompt typed by the host.
2. The system selects an unused prompt for the game. A prompt is never repeated
   within the same game. A typed prompt is also recorded as used.
3. The host selects an upload duration of 20, 40, or 60 seconds; the default is
   40 seconds.
4. The host starts the round. The system assigns the next round number, sets
   `upload_deadline` to server time now plus the selected duration, and changes
   the game phase to `uploading`.
5. During `uploading`, each known player may upload one JPEG photo no larger
   than 2 MB. The phone sends a JPEG reduced to at most 1600 px before upload.
6. A player may upload again before the deadline; the new photo replaces that
   player's previous photo for the round.
7. The host may add 10 seconds to the deadline or end uploads early.
8. Whenever game state is read, the system checks the server deadline. Uploads
   close when the deadline has passed, every player has uploaded, or the host
   ends uploads.
9. When uploads close with at least one photo, the system assigns a fixed
   random order to the photos, changes the phase to `voting`, and selects photo
   1 as the current photo for UC-003.
10. When uploads close with no photos, the system shows `No photos this round`
    and returns the game to `lobby`.

## Errors

- Starting a round outside `lobby` → 409.
- Empty typed prompt or invalid upload duration → 422.
- Upload outside `uploading` or after the deadline → 409 with message `Time's up`.
- Upload file is not JPEG → 422.
- Upload file is larger than 2 MB → 413.
- Missing or incorrect host token → 403.
- Unknown game or player → 404.

## Acceptance

Given a game in `lobby` phase and a valid host token  
When the host starts a round with a category, Shuffle, or valid custom prompt  
Then an unused prompt is recorded, the round is numbered, the deadline is
server time plus 20, 40, or 60 seconds, and the phase becomes `uploading`

Given a game with prompts already used in earlier rounds  
When the host previews or starts another category or Shuffle prompt  
Then the system does not select a prompt used earlier in that game

Given a game in `uploading` phase before its deadline  
When a player uploads a JPEG no larger than 2 MB  
Then the photo is stored for that player and the player may replace it by
uploading another photo before the deadline

Given a game in `uploading` phase after its server deadline  
When a player uploads a photo  
Then the server rejects it with status 409 and message `Time's up`

Given a game in `uploading` phase  
When the host adds 10 seconds or ends uploads early  
Then the deadline is extended by 10 seconds or uploads close immediately

Given uploads close with one or more photos  
When game state is read or the host closes uploads  
Then the photos receive one fixed random order, the phase becomes `voting`,
and photo 1 is current

Given uploads close with no photos  
When game state is read or the host closes uploads  
Then the system shows `No photos this round` and returns to `lobby`

Given an invalid host token, unknown game or unknown player, or an invalid file  
When the related action is requested  
Then the system returns the specified error status without changing game state

## Tests

- Unit: prompt selection excludes all prompts used in the game, including
  Shuffle and custom prompts.
- Unit: valid durations are exactly 20, 40, and 60 seconds, with 40 as default.
- Unit: deadline checks close uploads at expiry, and all-player completion closes
  uploads without a background job.
- Unit: photo replacement keeps only the player's latest upload before deadline.
- Unit: fixed random ordering is assigned once when uploads close.
- Integration: host starts category, Shuffle, and custom-prompt rounds and gets
  the round number, deadline, and `uploading` phase.
- Integration: invalid phase, prompt, duration, host token, game, player, file
  type, and file size return the specified errors.
- Integration: upload after the deadline is rejected by the server with 409
  `Time's up`.
- Integration: host extension and early close work, including deadline checks
  triggered by state reads.
- Integration: closing with photos enters `voting`; closing without photos shows
  `No photos this round` and returns to `lobby`.
- E2E: host starts a round, players upload or replace photos, the timer closes,
  and the projector enters voting in a stable random order.
