from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.infrastructure.database import init_db


def create_app(init_db: bool = True) -> FastAPI:
    app = FastAPI(title="PicMe API")

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

    return app
