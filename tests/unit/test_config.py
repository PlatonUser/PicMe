from app.infrastructure.config import normalize_database_url


def test_sqlite_database_url_stays_unchanged():
    url = "sqlite:///./app.db"

    assert normalize_database_url(url) == url


def test_postgres_database_urls_use_psycopg_driver():
    assert normalize_database_url("postgres://user:pass@localhost/db") == (
        "postgresql+psycopg://user:pass@localhost/db"
    )
    assert normalize_database_url("postgresql://user:pass@localhost/db") == (
        "postgresql+psycopg://user:pass@localhost/db"
    )
