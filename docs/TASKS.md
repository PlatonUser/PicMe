# TASKS.md

PHASE: 4
STATUS: done

(0=Bootstrap | 1=Specify | 2=Design | 3=Develop | 4=Validate | 5=Deploy)

Sprint: 3 (finish use cases, deploy, UI)

## UC-001

OWNER: A
PHASE: 3
STATUS: done

## UC-002

OWNER: A
PHASE: 3
STATUS: done

Prompt catalog in `src/app/domain/prompt.py`; round persistence, photo upload,
clock port, round service, round API and round-aware game state implemented.
Unit and integration tests pass (97 passed).

## UC-003

OWNER: A
PHASE: 3
STATUS: done

Votes table, VotingService and votes API (vote, progress, close voting, next photo,
back to lobby); unit, integration and e2e tests pass.

## UC-004

OWNER: A
PHASE: 3
STATUS: done

Scoring and competition ranking, ScoreService and scoreboard API (end, scoreboard,
play again); unit, integration and e2e tests pass.

## Validation

Command: `export PYTHONPATH=$PWD/src && pytest -q tests/unit tests/integration`
Result: **159 passed** (one existing `httpx`/Starlette deprecation warning).

Acceptance coverage for UC-001 to UC-004:

### UC-001

- Create game returns a valid code, host token, and `lobby`: `test_join_code_is_six_readable_characters`, `test_create_game_returns_join_code_host_token_and_lobby_phase` (integration), `test_create_game_returns_join_code_host_token_and_lobby_phase` (E2E) - **PASS**.
- Valid player join adds the player and returns a persistent id: `test_player_name_must_be_trimmed_and_between_one_and_twenty_characters`, `test_join_game_returns_player_id_and_trimmed_name` (integration), `test_player_joins_lobby_and_receives_persistent_player_id` (E2E) - **PASS**.
- Duplicate names are rejected case- and space-insensitively with the contract message: `test_player_names_are_unique_ignoring_case_and_spaces`, `test_duplicate_name_error_has_the_contract_message` (integration), `test_duplicate_name_ignores_case_and_spaces` (E2E) - **PASS**.
- Joining after leaving `lobby` returns 409: `test_players_can_join_only_in_lobby`, `test_joining_outside_lobby_is_rejected` (integration), `test_player_cannot_join_after_game_leaves_lobby` (E2E) - **PASS**.
- State returns phase, player names, and current round: `test_read_state_has_null_round_photo_and_voting_in_lobby`, `test_game_state_returns_phase_names_and_null_round_photo_and_voting` (integration), `test_game_state_returns_phase_players_and_current_round` (E2E) - **PASS**.

### UC-002

- Category, Shuffle, or custom prompt starts an unused numbered round with a valid server deadline in `uploading`: `test_start_round_selects_unused_prompt_and_assigns_number_and_deadline`, `test_round_accepts_only_supported_durations`, `test_round_defaults_to_forty_seconds`, `test_host_starts_category_shuffle_or_custom_round`, `test_round_uses_requested_duration_and_server_time` (integration), `test_start_round_selects_prompt_sets_deadline_and_enters_uploading` (E2E) - **PASS**.
- Previously used prompts are not selected again: `test_start_round_never_reuses_a_prompt_in_the_same_game`, `test_category_selection_excludes_prompts_already_used`, `test_shuffle_selection_excludes_prompts_used_across_categories`, `test_second_round_does_not_repeat_a_used_category_prompt`, `test_shuffle_round_does_not_repeat_prompt_used_by_earlier_rounds` (integration), `test_category_or_shuffle_does_not_repeat_a_prompt_in_one_game` (E2E) - **PASS**.
- A player can upload and replace a JPEG during uploading: `test_player_can_upload_a_jpeg_before_the_deadline`, `test_uploading_again_replaces_that_players_photo`, `test_player_uploads_and_replaces_a_jpeg` (integration), `test_player_uploads_and_replaces_jpeg_during_uploading` (E2E) - **PASS**.
- Upload after the server deadline is rejected with `Time's up`: `test_upload_after_the_deadline_is_rejected_with_times_up`, `test_upload_after_deadline_returns_times_up` (integration), `test_upload_after_uploads_close_returns_time_up_conflict` (E2E) - **PASS**.
- Host can extend by 10 seconds or close uploads early: `test_extend_adds_ten_seconds_to_the_deadline`, `test_host_can_close_uploads`, `test_host_extends_deadline_by_ten_seconds`, `test_host_closes_round_with_photos_and_sets_first_current_photo` (integration), `test_host_can_extend_deadline_or_close_uploads_early` (E2E) - **PASS**.
- Closing with photos enters voting with fixed order and photo 1 current: `test_closing_assigns_positions_using_the_shuffle_function`, `test_closing_does_not_reshuffle_already_positioned_photos`, `test_host_closes_round_with_photos_and_sets_first_current_photo` (integration), `test_closing_with_photos_enters_voting_with_first_photo_current` (E2E) - **PASS**.
- Closing without photos returns to lobby with `No photos this round`: `test_closing_with_no_photos_returns_to_lobby_with_a_message`, `test_host_closes_round_without_photos_and_returns_to_lobby` (integration), `test_closing_without_photos_returns_no_photos_message_and_lobby` (E2E) - **PASS**.

### UC-003

- Eligible players can submit and change a guess, retaining only the latest: `test_voter_keeps_only_the_latest_guess_for_the_photo`, `test_eligible_player_guess_is_recorded_and_can_be_changed` (E2E) - **PASS**.
- Host vote progress exposes counts without individual guesses: `test_progress_returns_only_voted_count_and_eligible_total`, `test_host_can_read_vote_progress_during_voting` (integration), `test_vote_progress_exposes_counts_without_individual_guesses` (E2E) - **PASS**.
- Last eligible vote automatically enters reveal and shows uploader: `test_voting_is_complete_when_every_eligible_voter_has_guessed`, `test_last_eligible_vote_changes_phase_to_reveal_automatically`, `test_last_eligible_vote_enters_reveal_and_shows_uploader` (E2E) - **PASS**.
- Host can close voting with pending votes and reveal uploader: `test_host_can_close_voting_and_reveal_uploader` (integration), `test_host_closes_voting_with_pending_votes_and_reveals_uploader` (E2E) - **PASS**.
- Host can advance reveal to the next photo and return to voting: `test_next_photo_moves_to_voting_for_the_next_photo`, `test_host_can_advance_to_the_next_photo` (integration), `test_host_advances_reveal_to_voting_for_next_photo` (E2E) - **PASS**.
- After the last photo, host can return to lobby: `test_return_to_lobby_after_last_reveal_sets_phase_lobby`, `test_host_can_return_to_lobby_after_last_reveal` (integration), `test_host_returns_to_lobby_after_last_photo` (E2E) - **PASS**.
- Voting rejects uploader guesses, invalid players, wrong phase, unknown resources, and invalid host tokens: `test_uploader_cannot_guess_their_own_photo`, `test_guess_must_name_a_player_in_the_game`, `test_voting_outside_the_voting_phase_raises_conflict`, `test_submit_guess_returns_403_when_voter_is_the_uploader`, `test_submit_guess_returns_422_when_guessed_player_is_not_in_game`, `test_missing_or_wrong_host_token_on_every_host_action_returns_403_and_preserves_state` (integration), `test_voting_errors_cover_uploader_invalid_guess_wrong_phase_and_unknown_game`, `test_voting_host_actions_require_the_host_token` (E2E) - **PASS**.

### UC-004

- Returning to lobby after the last reveal preserves accumulated scores: `test_returning_to_lobby_between_rounds_keeps_points`, `test_host_returns_to_lobby_after_last_reveal_preserving_scores` (integration), `test_last_reveal_can_return_to_lobby_preserving_game_players` (E2E) - **PASS**.
- Correct eligible guesses score one point, excluding the uploader, across rounds: `test_correct_guesses_score_one_point_except_for_uploader_and_wrong_guesses`, `test_points_accumulate_over_several_photos_and_rounds`, `test_complete_game_ends_with_points_ranked_scoreboard_and_correct_me` (E2E) - **PASS**.
- Points and ranks are hidden before scoreboard: `test_state_never_contains_points_or_ranks_in_any_phase` (integration), `test_state_hides_points_and_ranks_before_scoreboard` (E2E) - **PASS**.
- Ending after the last photo enters scoreboard: `test_end_game_sets_scoreboard_and_scores_correct_eligible_guesses`, `test_host_can_end_game_and_read_full_scoreboard` (integration), `test_complete_game_ends_with_points_ranked_scoreboard_and_correct_me` (E2E) - **PASS**.
- Competition ranking assigns 1, 2, 2, 4 for 10, 7, 7, 3: `test_scoreboard_uses_competition_ranking_for_ties` - **PASS**.
- Player scoreboard includes own rank/points and the full sorted list: `test_scoreboard_returns_full_ranked_list_and_me_with_competition_ranks`, `test_host_can_end_game_and_read_full_scoreboard` (integration), `test_complete_game_ends_with_points_ranked_scoreboard_and_correct_me` (E2E) - **PASS**.
- Play again preserves players, removes round data, resets scores, and returns to lobby: `test_play_again_preserves_players_deletes_game_data_and_resets_scores`, `test_play_again_resets_to_lobby_keeps_players_and_removes_round_data` (integration), `test_play_again_preserves_players_resets_game_to_lobby_and_hides_old_scoreboard` (E2E) - **PASS**.

Manual validation: full game played on the live URL with phones on 2026-10-27; all acceptance flows worked.

## Delivery (acceptance tests, deployment, UI)

OWNER: B
PHASE: 4
STATUS: done

acceptance tests, deployment (Render + Neon, CD), host and player UI
