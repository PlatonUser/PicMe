from collections.abc import Callable

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel

from app.application.voting_service import VotingService


class VoteRequest(BaseModel):
    player_id: int
    guessed_player_id: int


def router(service_dependency: Callable[..., VotingService]) -> APIRouter:
    api = APIRouter()

    @api.post("/games/{code}/votes", status_code=201)
    def vote(code: str, request: VoteRequest,
             service: VotingService = Depends(service_dependency)):
        vote_result = service.vote(
            code, request.player_id, request.guessed_player_id
        )
        return {"accepted": vote_result.accepted}

    @api.get("/games/{code}/votes/progress")
    def progress(code: str, x_host_token: str | None = Header(default=None),
                 service: VotingService = Depends(service_dependency)):
        progress_result = service.progress(code, x_host_token or "")
        return {"voted": progress_result.voted,
                "eligible": progress_result.eligible}

    @api.post("/games/{code}/voting/close")
    def close(code: str, x_host_token: str | None = Header(default=None),
              service: VotingService = Depends(service_dependency)):
        close_result = service.close_voting(code, x_host_token or "")
        return {"phase": close_result.phase,
                "uploader_name": close_result.uploader_name}

    @api.post("/games/{code}/photos/next")
    def next_photo(code: str, x_host_token: str | None = Header(default=None),
                   service: VotingService = Depends(service_dependency)):
        next_photo_result = service.next_photo(code, x_host_token or "")
        return {"phase": next_photo_result.phase,
                "position": next_photo_result.position}

    @api.post("/games/{code}/lobby")
    def lobby(code: str, x_host_token: str | None = Header(default=None),
              service: VotingService = Depends(service_dependency)):
        lobby_result = service.return_to_lobby(code, x_host_token or "")
        return {"phase": lobby_result.phase}

    return api
