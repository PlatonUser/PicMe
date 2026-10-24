from collections.abc import Callable

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.application.game_service import GameService
from app.domain.time import as_utc


class JoinGameRequest(BaseModel):
    name: str


def router(service_dependency: Callable[..., GameService]) -> APIRouter:
    api = APIRouter(prefix="/games")

    @api.post("", status_code=201)
    def create_game(service: GameService = Depends(service_dependency)):
        game = service.create_game()
        return {"code": game.code, "host_token": game.host_token, "phase": game.phase}

    @api.post("/{code}/players", status_code=201)
    def join_game(
        code: str,
        request: JoinGameRequest,
        service: GameService = Depends(service_dependency),
    ):
        player = service.join_game(code, request.name)
        return {"player_id": player.id, "name": player.name}

    @api.get("/{code}/state")
    def game_state(code: str, service: GameService = Depends(service_dependency)):
        state = service.state(code)
        if state["round"] is not None:
            state["round"]["upload_deadline"] = as_utc(state["round"]["upload_deadline"])
            state["round"]["server_time"] = as_utc(state["round"]["server_time"])
        return state

    return api
