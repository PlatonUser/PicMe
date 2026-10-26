def calculate_scores(players: dict[int, str], photos: list[dict]) -> dict[int, int]:
    scores = {player_id: 0 for player_id in players}

    for photo in photos:
        uploader_id = photo["uploader_id"]
        for voter_id, guessed_id in photo["guesses"].items():
            if voter_id != uploader_id and guessed_id == uploader_id:
                scores[voter_id] += 1

    return scores


def rank_scoreboard(scores: dict[int, int]) -> list[dict[str, int]]:
    ranked_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    scoreboard = []
    previous_points = None

    for position, (player_id, points) in enumerate(ranked_scores, start=1):
        if points != previous_points:
            rank = position
            previous_points = points
        scoreboard.append({"player_id": player_id, "points": points, "rank": rank})

    return scoreboard
