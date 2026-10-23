from types import SimpleNamespace

from services.readiness import ReadinessService


class FakeConnection:
    def __init__(self, *, fails=False):
        self.fails = fails

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, _statement):
        if self.fails:
            raise RuntimeError("database unavailable")


class FakeEngine:
    def __init__(self, *, fails=False):
        self.fails = fails

    def connect(self):
        return FakeConnection(fails=self.fails)


def test_database_failure_blocks_readiness_without_leaking_details():
    readiness = ReadinessService(database_engine=FakeEngine(fails=True), production=False)

    result = readiness.check()

    assert result == {
        "ready": False,
        "degraded": False,
        "components": {"database": False},
    }


def test_noncritical_dependency_failure_reports_degraded_but_stays_ready():
    def unavailable():
        raise RuntimeError("dependency unavailable")

    readiness = ReadinessService(
        database_engine=FakeEngine(),
        production=True,
        dependency_probes={"evidence_storage": unavailable},
    )

    result = readiness.check()

    assert result["ready"] is True
    assert result["degraded"] is True
    assert result["components"]["evidence_storage"] is False


def test_external_dependency_probes_are_cached_until_expiration():
    state = SimpleNamespace(now=100.0, calls=0)

    def probe():
        state.calls += 1

    readiness = ReadinessService(
        database_engine=FakeEngine(),
        production=True,
        cache_seconds=30,
        clock=lambda: state.now,
        dependency_probes={"authentication_limiter": probe},
    )

    readiness.check()
    readiness.check()
    assert state.calls == 1

    state.now = 131.0
    readiness.check()
    assert state.calls == 2
