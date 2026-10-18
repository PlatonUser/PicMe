import os

from dotenv import load_dotenv


load_dotenv()

DEFAULT_DATABASE_URL = "sqlite:///./app.db"


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


DATABASE_URL = normalize_database_url(
    os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
)
