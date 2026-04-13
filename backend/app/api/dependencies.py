from sqlalchemy.orm import Session

from app.db.session import get_db


def db_session_dependency() -> Session:
    yield from get_db()

