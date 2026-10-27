from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_case_timeline_request_is_authenticated_and_not_duplicated():
    source = (
        REPOSITORY_ROOT
        / "beaconsystems.client"
        / "src"
        / "pages"
        / "CaseDetail.jsx"
    ).read_text(encoding="utf-8")

    timeline_request = 'fetch(apiUrl(`/timeline-events/?case_id=${id}`), {'
    assert timeline_request in source
    request_section = source[source.index(timeline_request):]
    assert "headers: authHeaders" in request_section[:250]
    assert "const unifiedTimeline = timelineEvents" in source
    assert "timelineEvents.length + sortedSightings.length" not in source
    assert "unifiedTimeline.map((event)" in source


def test_manually_created_timeline_events_are_audited_and_case_scoped():
    source = (
        REPOSITORY_ROOT / "routes" / "timeline_events_routes.py"
    ).read_text(encoding="utf-8")

    assert "assert_case_write_access(db, data.case_id, current_user)" in source
    assert "get_authorized_case(db, case_id, current_user)" in source
    assert 'action="CREATE_TIMELINE_EVENT"' in source
    assert 'entity="timeline_event"' in source
