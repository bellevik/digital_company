from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Digital Company"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    worker_memory_window: int = 5
    memory_embedding_dimensions: int = 1536
    memory_search_candidate_limit: int = 25
    scheduler_enabled: bool = False
    self_improvement_interval_seconds: int = 86400
    self_improvement_branch_prefix: str = "codex/self-improvement"

    codex_execution_backend: str = "codex_cli"
    codex_cli_command: str = "codex"
    codex_cli_subcommand: str = "exec"
    codex_cli_full_auto_flag: str = "--full-auto"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "digital_company"
    postgres_user: str = "digital_company"
    postgres_password: str = "digital_company"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            "postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
