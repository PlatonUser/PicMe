from app.domain.scoring import calculate_scores, rank_scoreboard


def test_correct_guesses_score_one_point_except_for_uploader_and_wrong_guesses():
    players = {1: "Anna", 2: "Ben", 3: "Cara"}
    photos = [
        {"uploader_id": 1, "guesses": {1: 1, 2: 1, 3: 2}},
    ]

    assert calculate_scores(players, photos) == {1: 0, 2: 1, 3: 0}


def test_points_accumulate_over_several_photos_and_rounds():
    players = {1: "Anna", 2: "Ben", 3: "Cara"}
    photos = [
        {"uploader_id": 1, "guesses": {2: 1, 3: 1}},
        {"uploader_id": 2, "guesses": {1: 2, 3: 3}},
        {"uploader_id": 3, "guesses": {1: 3, 2: 3}},
    ]

    # Anna: Ben's + Cara's photo; Ben: Anna's + Cara's; Cara: only Anna's (guessed herself on Ben's)
    assert calculate_scores(players, photos) == {1: 2, 2: 2, 3: 1}


def test_players_without_correct_guesses_keep_zero_points_in_scoreboard():
    players = {1: "Anna", 2: "Ben", 3: "Cara"}
    photos = [{"uploader_id": 1, "guesses": {2: 1}}]

    assert calculate_scores(players, photos) == {1: 0, 2: 1, 3: 0}


def test_scoreboard_is_sorted_highest_points_first():
    scores = {1: 3, 2: 10, 3: 7}

    assert rank_scoreboard(scores) == [
        {"player_id": 2, "points": 10, "rank": 1},
        {"player_id": 3, "points": 7, "rank": 2},
        {"player_id": 1, "points": 3, "rank": 3},
    ]


def test_scoreboard_uses_competition_ranking_for_ties():
    scores = {1: 10, 2: 7, 3: 7, 4: 3}

    assert [entry["rank"] for entry in rank_scoreboard(scores)] == [1, 2, 2, 4]


def test_all_zero_scores_share_first_rank():
    scores = {1: 0, 2: 0, 3: 0}

    assert [entry["rank"] for entry in rank_scoreboard(scores)] == [1, 1, 1]
