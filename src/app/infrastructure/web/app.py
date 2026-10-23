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
from app.infrastructure.persistence.sqlalchemy_photo_storage import SQLAlchemyPhotoStorage
from app.infrastructure.system_clock import SystemClock


def create_app(init_db: bool = True) -> FastAPI:
    app = FastAPI(title="PicMe API")
    session = SessionLocal()
    game_repository = SQLAlchemyGameRepository(session)
    app.state.round_service = RoundService(
        game_repository,
        SQLAlchemyRoundRepository(session),
        SQLAlchemyPhotoStorage(session),
        SystemClock(),
    )
    app.state.game_service = GameService(game_repository, app.state.round_service.state)

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
