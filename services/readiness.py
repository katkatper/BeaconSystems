import logging
import threading
import time
from collections.abc import Callable

from sqlalchemy import text as sql_text

from config.settings import IS_PRODUCTION, READINESS_DEPENDENCY_CACHE_SECONDS
from database.connection import engine
from security.rate_limit import validate_rate_limit_backend
from services.malware_scanner import malware_scanner
from services.object_storage import object_storage

logger = logging.getLogger("beacon.readiness")


class ReadinessService:
    """Check critical readiness and cache slower dependency probes."""

    def __init__(
        self,
        *,
        database_engine=engine,
        production: bool = IS_PRODUCTION,
        cache_seconds: float = READINESS_DEPENDENCY_CACHE_SECONDS,
        clock: Callable[[], float] = time.monotonic,
        dependency_probes: dict[str, Callable[[], None]] | None = None,
    ):
        self.database_engine = database_engine
        self.production = production
        self.cache_seconds = cache_seconds
        self.clock = clock
        self.dependency_probes = dependency_probes or {
            "authentication_limiter": validate_rate_limit_backend,
            "evidence_storage": object_storage.validate_production_access,
            "malware_scanner": malware_scanner.validate_production_access,
        }
        self._dependency_results: dict[str, bool] = {}
        self._dependency_expires_at = 0.0
        self._lock = threading.Lock()

    @staticmethod
    def _run_probe(name: str, probe: Callable[[], None]) -> bool:
        try:
            probe()
            return True
        except Exception:
            logger.exception(
                "Production dependency readiness probe failed",
                extra={"readiness_component": name},
            )
            return False

    def _check_dependencies(self, *, force: bool = False) -> dict[str, bool]:
        if not self.production:
            return {}

        now = self.clock()
        with self._lock:
            if not force and now < self._dependency_expires_at:
                return dict(self._dependency_results)
            self._dependency_results = {
                name: self._run_probe(name, probe)
                for name, probe in self.dependency_probes.items()
            }
            self._dependency_expires_at = now + self.cache_seconds
            return dict(self._dependency_results)

    def check(self, *, force_dependencies: bool = False) -> dict:
        database_ready = self._run_probe("database", self._check_database)
        dependencies = self._check_dependencies(force=force_dependencies)
        return {
            "ready": database_ready,
            "degraded": any(not ready for ready in dependencies.values()),
            "components": {"database": database_ready, **dependencies},
        }

    def _check_database(self) -> None:
        with self.database_engine.connect() as connection:
            connection.execute(sql_text("SELECT 1"))


readiness_service = ReadinessService()
