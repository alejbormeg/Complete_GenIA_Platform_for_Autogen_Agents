import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional
from dataclasses import dataclass
from tenacity import retry, stop_after_delay, wait_exponential, before_log, after_log
from dotenv import load_dotenv

# Load .env for local dev; in containers Compose env wins because override=False
load_dotenv(override=False)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    # Register pgvector adapter for psycopg2
    from pgvector.psycopg2 import register_vector
except Exception as e:
    logger.warning("pgvector adapter not available: %s", e)
    register_vector = None


@dataclass
class PGConfig:
    host: str
    port: int
    db: str
    user: str
    password: str
    sslmode: Optional[str] = None
    application_name: str = "backend"

    @classmethod
    def from_env(cls) -> "PGConfig":
        return cls(
            host=os.getenv("POSTGRES_HOST", "db"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            db=os.getenv("POSTGRES_DB", "postgres"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            sslmode=os.getenv("POSTGRES_SSLMODE", None),
            application_name=os.getenv("PGAPPNAME", "backend"),
        )

    def dsn(self) -> str:
        parts = [
            f"host={self.host}",
            f"port={self.port}",
            f"dbname={self.db}",
            f"user={self.user}",
            f"password={self.password}",
            f"application_name={self.application_name}",
        ]
        if self.sslmode:
            parts.append(f"sslmode={self.sslmode}")
        return " ".join(parts)


def ensure_pgvector(conn) -> None:
    """Create extension pgvector and register adapter."""
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.commit()
    if register_vector:
        register_vector(conn)


@retry(
    stop=stop_after_delay(60),                 # try for up to 60s
    wait=wait_exponential(multiplier=1, min=1, max=5),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.INFO),
    reraise=True,
)
def open_pg_connection():
    """Open a psycopg2 connection with retries until DB is ready."""
    cfg = PGConfig.from_env()
    logger.info("Connecting to Postgres at %s:%s db=%s user=%s",
                cfg.host, cfg.port, cfg.db, cfg.user)
    conn = psycopg2.connect(dsn=cfg.dsn(), cursor_factory=RealDictCursor)
    ensure_pgvector(conn)
    return conn


# Expose a tiny service container you were importing elsewhere
@dataclass
class AppServices:
    pg_conn: "psycopg2.extensions.connection"

def build_services() -> AppServices:
    conn = open_pg_connection()
    return AppServices(pg_conn=conn)
