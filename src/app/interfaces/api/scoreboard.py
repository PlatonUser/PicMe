from collections.abc import Callable

from fastapi import APIRouter, Depends, Header, Query

from app.application.score_service import ScoreService


def router(service_dependency: Callable[..., ScoreService]) -> APIRouter:
    api = APIRouter()

    @api.post("/games/{code}/end")
    def end(code: str, x_host_token: str | None = Header(default=None),
            service: ScoreService = Depends(service_dependency)):
        return {"phase": service.end_game(code, x_host_token or "").phase}

    @api.get("/games/{code}/scoreboard")
    def scoreboard(code: str, player_id: int = Query(...),
                   service: ScoreService = Depends(service_dependency)):
        return service.scoreboard(code, player_id)

    @api.post("/games/{code}/play-again")
    def play_again(code: str, x_host_token: str | None = Header(default=None),
                   service: ScoreService = Depends(service_dependency)):
        return {"phase": service.play_again(code, x_host_token or "").phase}

    return api
