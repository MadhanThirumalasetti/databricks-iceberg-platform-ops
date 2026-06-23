import logging
import psycopg2
from dataclasses import dataclass
from typing import List
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class RedshiftConfig:
    host: str
    port: int = 5439
    database: str = "analytics"
    user: str = "admin"
    password: str = ""
    sslmode: str = "require"


class RedshiftUserManager:

    def __init__(self, config: RedshiftConfig):
        self.config = config

    @contextmanager
    def get_connection(self):
        conn = psycopg2.connect(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.user,
            password=self.config.password,
            sslmode=self.config.sslmode,
        )
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_user(self, username: str, password: str, groups: List[str] = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"CREATE USER {username} PASSWORD %s;", (password,))
            logger.info(f"Created user: {username}")
            if groups:
                for group in groups:
                    cursor.execute(f"ALTER GROUP {group} ADD USER {username};")
                    logger.info(f"Added {username} to group {group}")

    def grant_schema_access(self, group_name: str, schema: str, privileges: List[str] = None):
        if privileges is None:
            privileges = ["SELECT"]
        priv_str = ", ".join(privileges)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"GRANT USAGE ON SCHEMA {schema} TO GROUP {group_name};")
            cursor.execute(f"GRANT {priv_str} ON ALL TABLES IN SCHEMA {schema} TO GROUP {group_name};")
            cursor.execute(
                f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} "
                f"GRANT {priv_str} ON TABLES TO GROUP {group_name};"
            )
            logger.info(f"Granted {priv_str} on schema {schema} to group {group_name}")

    def get_slow_queries(self, min_duration_seconds: int = 30, limit: int = 20):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    q.query,
                    TRIM(qt.querytxt) AS query_text,
                    q.elapsed / 1000000.0 AS elapsed_seconds,
                    q.rows,
                    q.starttime
                FROM stl_query q
                JOIN stl_querytext qt ON q.query = qt.query AND qt.sequence = 0
                WHERE q.elapsed > %s * 1000000
                    AND q.aborted = 0
                ORDER BY q.elapsed DESC
                LIMIT %s;
            """, (min_duration_seconds, limit))
            return cursor.fetchall()
