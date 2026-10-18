# UC-001-CREATE-AND-JOIN-GAME

## Intent

Allow a host to start a PicMe game and allow players to join it using a short,
readable join code.

## Actors

- Host: creates a new game and receives the join code and host token.
- Player: joins an existing game with a name.
- Reader: anyone with the join code reads game state.

## Preconditions

No prior state required.

## Flow

1. Host requests creation of a new game.
2. System generates:
   - a 6-character join code from capital letters and digits, excluding look-alike
     characters O/0 and I/1;
   - a secret host token.
3. System stores the game with phase `lobby` and returns the join code and host token.
4. Player submits the join code and a name.
5. System validates the name:
   - trims whitespace from both ends;
   - requires 1-20 characters after trimming.
6. System checks name uniqueness within the game, ignoring case and spaces.
7. System assigns the player a persistent player id and adds the player to the game.
8. System returns the player id.
9. A client with the player id may refresh the page and remain in the game.
10. Anyone with the join code may read the game state:
    - phase;
    - player names;
    - current round, if one exists.

## Errors

- Unknown join code → 404.
- Empty or too long name (>20 trimmed characters) → 422.
- Name already taken within the game (case- and space-insensitive) → 409 with message
  `That name is taken. Add an initial.`
- Join attempt when the game is not in `lobby` phase → 409.

## Acceptance

Given no game exists  
When a host creates a game  
Then the system returns a valid join code and host token, and the game phase is `lobby`

Given a game in `lobby` phase  
When a player joins with a valid name  
Then the player is added and receives a player id

Given a game with an existing player  
When another player tries to join with a name matching when case and spaces are ignored  
Then the request is rejected with status 409 and message `That name is taken. Add an initial.`

Given a game not in `lobby` phase  
When a player tries to join  
Then the request is rejected with status 409

Given a game with players  
When anyone reads the game state with the join code  
Then the phase, player names, and current round are returned

## Tests

- Unit: join code generation excludes O/0/I/1 and is 6 characters long.
- Unit: name validation trims and enforces 1-20 character limit.
- Unit: name uniqueness comparison ignores case and spaces.
- Integration: create game returns join code + host token and lobby state.
- Integration: join with invalid name returns 422.
- Integration: join with duplicate name returns 409 with correct message.
- Integration: join outside lobby returns 409.
- Integration: read game state returns phase, names, and current round.
- E2E: host creates a game, player joins, page refresh keeps player in game.
