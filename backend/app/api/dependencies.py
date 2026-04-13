from functools import lru_cache

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_db
from app.services.execution import CodexCLIExecutionAdapter, ExecutionAdapter, MockExecutionAdapter


def db_session_dependency() -> Session:
    yield from get_db()


@lru_cache
def _build_execution_adapter() -> ExecutionAdapter:
    settings = get_settings()
    if settings.codex_execution_backend == "mock":
        return MockExecutionAdapter()
    return CodexCLIExecutionAdapter(settings=settings)


def execution_adapter_dependency() -> ExecutionAdapter:
    return _build_execution_adapter()
