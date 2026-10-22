from fastapi import APIRouter, Depends, File, Form, Header, UploadFile
from pydantic import BaseModel

from app.application.round_service import RoundService
from app.domain.prompt import CATEGORIES
from app.infrastructure.system_clock import SystemClock


class StartRoundRequest(BaseModel):
    category: str | None = None
    prompt: str | None = None
    duration: int = 40


def get_clock():
    return SystemClock()


def router(service: RoundService) -> APIRouter:
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
        clock=Depends(get_clock),
    ):
        service.clock = clock
        result = service.start_round(
            code, x_host_token or "", request.category, request.prompt, request.duration
        )
        return {
            "round_number": result.round_number,
            "prompt": result.prompt,
            "category": result.category,
            "hint": result.hint,
            "upload_deadline": result.upload_deadline,
            "phase": result.phase,
        }

    @api.post("/games/{code}/rounds/current/photos", status_code=201)
    async def upload_photo(
        code: str,
        player_id: int = Form(...),
        photo: UploadFile = File(...),
        clock=Depends(get_clock),
    ):
        service.clock = clock
        result = service.upload_photo(code, player_id, await photo.read())
        return {"photo_id": result.photo_id, "player_id": result.player_id}

    @api.post("/games/{code}/rounds/current/extend")
    def extend_round(
        code: str,
        x_host_token: str | None = Header(default=None),
        clock=Depends(get_clock),
    ):
        service.clock = clock
        return {"upload_deadline": service.extend_round(code, x_host_token or "")}

    @api.post("/games/{code}/rounds/current/close")
    def close_round(
        code: str,
        x_host_token: str | None = Header(default=None),
        clock=Depends(get_clock),
    ):
        service.clock = clock
        result = service.close_round(code, x_host_token or "")
        response = {"phase": result.phase}
        if result.message:
            response["message"] = result.message
        return response

    @api.get("/photos/{photo_id}/image")
    def image(photo_id: int):
        from fastapi.responses import Response

        return Response(service.image(photo_id), media_type="image/jpeg")

    return api
