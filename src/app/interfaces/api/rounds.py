from collections.abc import Callable

from fastapi import APIRouter, Depends, File, Form, Header, UploadFile
from pydantic import BaseModel

from app.application.round_service import RoundService
from app.domain.prompt import CATEGORIES
from app.domain.time import as_utc


class StartRoundRequest(BaseModel):
    category: str | None = None
    prompt: str | None = None
    duration: int = 40


def router(service_dependency: Callable[..., RoundService]) -> APIRouter:
    api = APIRouter()

    @api.get("/prompts/categories")
    def categories():
        return [{"id": category.id, "name": category.name} for category in CATEGORIES] + [
            {"id": "shuffle", "name": "Shuffle"}
        ]

    @api.post("/games/{code}/rounds", status_code=201)
    def start_round(
        code: str,
        request: StartRoundRequest,
        x_host_token: str | None = Header(default=None),
        service: RoundService = Depends(service_dependency),
    ):
        result = service.start_round(
            code, x_host_token or "", request.category, request.prompt, request.duration
        )
        return {
            "round_number": result.round_number,
            "prompt": result.prompt,
            "category": result.category,
            "hint": result.hint,
            "upload_deadline": as_utc(result.upload_deadline),
            "phase": result.phase,
        }

    @api.post("/games/{code}/rounds/current/photos", status_code=201)
    async def upload_photo(
        code: str,
        player_id: int = Form(...),
        photo: UploadFile = File(...),
        service: RoundService = Depends(service_dependency),
    ):
        result = service.upload_photo(code, player_id, await photo.read())
        return {"photo_id": result.photo_id, "player_id": result.player_id}

    @api.post("/games/{code}/rounds/current/extend")
    def extend_round(
        code: str,
        x_host_token: str | None = Header(default=None),
        service: RoundService = Depends(service_dependency),
    ):
        return {"upload_deadline": as_utc(service.extend_round(code, x_host_token or ""))}

    @api.post("/games/{code}/rounds/current/close")
    def close_round(
        code: str,
        x_host_token: str | None = Header(default=None),
        service: RoundService = Depends(service_dependency),
    ):
        result = service.close_round(code, x_host_token or "")
        response = {"phase": result.phase}
        if result.message:
            response["message"] = result.message
        return response

    @api.get("/photos/{photo_id}/image")
    def image(photo_id: int, service: RoundService = Depends(service_dependency)):
        from fastapi.responses import Response

        return Response(service.image(photo_id), media_type="image/jpeg")

    return api
