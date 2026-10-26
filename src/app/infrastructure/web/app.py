from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.infrastructure.database import SessionLocal, get_db, init_db
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
from app.infrastructure.persistence.sqlalchemy_game_repository import (
    SQLAlchemyGameRepository,
)
from app.interfaces.api.games import router as games_router
from app.interfaces.api.rounds import router as rounds_router
from app.application.round_service import RoundService
from app.infrastructure.persistence.sqlalchemy_round_repository import SQLAlchemyRoundRepository
from app.infrastructure.persistence.sqlalchemy_photo_storage import SQLAlchemyPhotoStorage
from app.infrastructure.system_clock import SystemClock
from app.application.voting_service import VotingService
from app.infrastructure.persistence.sqlalchemy_vote_repository import SQLAlchemyVoteRepository
from app.interfaces.api.votes import router as votes_router
from app.application.score_service import ScoreService
from app.interfaces.api.scoreboard import router as scoreboard_router


def create_app(init_db: bool = True) -> FastAPI:
    app = FastAPI(title="PicMe API")
    app.state.game_service = GameServiceController()

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

    @app.get("/host", include_in_schema=False)
    def host_page() -> FileResponse:
        return FileResponse("src/app/infrastructure/web/static/host.html")

    @app.get("/play", include_in_schema=False)
    def play_page() -> FileResponse:
        return FileResponse("src/app/infrastructure/web/static/play.html")

    app.mount(
        "/ui",
        StaticFiles(directory="src/app/infrastructure/web/static", html=True),
        name="ui",
    )

    if init_db:
        from app.infrastructure.database import init_db as initialize_db

        initialize_db()

    app.include_router(games_router(get_game_service))
    app.include_router(rounds_router(get_round_service))
    app.include_router(votes_router(get_voting_service))
    app.include_router(scoreboard_router(get_score_service))

    return app


def get_clock() -> SystemClock:
    return SystemClock()


def get_round_service(
    session=Depends(get_db),
    clock=Depends(get_clock),
) -> RoundService:
    game_repository = SQLAlchemyGameRepository(session)
    return RoundService(
        game_repository,
        SQLAlchemyRoundRepository(session),
        SQLAlchemyPhotoStorage(session),
        clock,
    )


def get_voting_service(
    session=Depends(get_db),
    clock=Depends(get_clock),
) -> VotingService:
    games = SQLAlchemyGameRepository(session)
    rounds = SQLAlchemyRoundRepository(session)
    return VotingService(games, rounds, SQLAlchemyVoteRepository(session),
                         SQLAlchemyPhotoStorage(session), clock)


def get_game_service(
    session=Depends(get_db),
    round_service: RoundService = Depends(get_round_service),
    voting_service: VotingService = Depends(get_voting_service),
) -> GameService:
    def state(code: str) -> dict:
        return voting_service.state(code, round_service.state(code))

    return GameService(SQLAlchemyGameRepository(session), state)


def get_score_service(session=Depends(get_db)) -> ScoreService:
    return ScoreService(
        SQLAlchemyGameRepository(session),
        SQLAlchemyRoundRepository(session),
        SQLAlchemyVoteRepository(session),
    )


class GameServiceController:
    """Provide explicit, out-of-request mutations for infrastructure callers."""

    def set_phase(self, code: str, phase: str) -> None:
        session = SessionLocal()
        try:
            GameService(SQLAlchemyGameRepository(session)).set_phase(code, phase)
        finally:
            session.close()
