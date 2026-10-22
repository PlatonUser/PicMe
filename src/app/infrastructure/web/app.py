from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.infrastructure.database import init_db
from app.domain.errors import (
    Conflict,
    Forbidden,
    InvalidInput,
    NotFound,
    PayloadTooLarge,
)
from app.infrastructure.web.errors import (
    conflict_handler,
    forbidden_handler,
    invalid_input_handler,
    not_found_handler,
    payload_too_large_handler,
)
from app.application.game_service import GameService
from app.infrastructure.database import SessionLocal
from app.infrastructure.persistence.sqlalchemy_game_repository import (
    SQLAlchemyGameRepository,
)
from app.interfaces.api.games import router as games_router
from app.interfaces.api.rounds import router as rounds_router, get_clock
from app.application.round_service import RoundService
from app.infrastructure.persistence.sqlalchemy_round_repository import SQLAlchemyRoundRepository
from app.infrastructure.system_clock import SystemClock


def create_app(init_db: bool = True) -> FastAPI:
    app = FastAPI(title="PicMe API")
    session = SessionLocal()
    app.state.game_service = GameService(SQLAlchemyGameRepository(session))
    app.state.round_service = RoundService(app.state.game_service.repository, SQLAlchemyRoundRepository(session), MemoryPhotoStorage(), SystemClock())
    app.state.game_service.round_service = app.state.round_service

    app.add_exception_handler(NotFound, not_found_handler)
    app.add_exception_handler(Conflict, conflict_handler)
    app.add_exception_handler(InvalidInput, invalid_input_handler)
    app.add_exception_handler(Forbidden, forbidden_handler)
    app.add_exception_handler(PayloadTooLarge, payload_too_large_handler)

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/ui")

    @app.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "healthy"}

    app.mount(
        "/ui",
        StaticFiles(directory="src/app/infrastructure/web/static", html=True),
        name="ui",
    )

    if init_db:
        from app.infrastructure.database import init_db as initialize_db

        initialize_db()

    app.include_router(games_router(app.state.game_service))
    app.include_router(rounds_router(app.state.round_service))

    return app


class MemoryPhotoStorage:
    def __init__(self):
        self.photos = {}

    def store(self, photo_id, data):
        self.photos[photo_id] = data

    def get(self, photo_id):
        return self.photos[photo_id]

