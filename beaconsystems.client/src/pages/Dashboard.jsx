import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet } from "../api.jsx";
import { getVisibleCount, markItemViewed, subscribeToReadState } from "../commandCenterState.js";
import OperationsMap from "./OperationsMap.jsx";



function Dashboard() {
    const [summary, setSummary] = useState(null);
    const [supervisorQueue, setSupervisorQueue] = useState(null);
    const [showAllActionItems, setShowAllActionItems] = useState(false);
    const [currentTime, setCurrentTime] = useState(() => new Date());
    const [, setReadStateVersion] = useState(0);
    const [error, setError] = useState(
        localStorage.getItem("token") ? "" : "No login token found. Please log in first."
    );
    const role = localStorage.getItem("role") || "viewer";
    const username = localStorage.getItem("username") || "Beacon User";
    const dashboardProfiles = {
        admin: {
            title: "Command Center",
            greeting: `Administrator overview for ${username}`,
            showBolos: true,
            showEvidence: true,
            actions: [
                ["Legal Order", "/legal-orders"],
                ["Alert", "/alerts"],
                ["Personnel", "/supervisor/personnel"],
                ["Audit Center", "/audit"],
                ["Evidence", "/evidence-upload"],
                ["Partners", "/partner-sources"],
            ],
        },
        agency_admin: {
            title: "Supervisor Operations",
            greeting: `Agency oversight queue for ${username}`,
            showBolos: true,
            showEvidence: true,
            actions: [
                ["Legal Order", "/legal-orders"],
                ["Alert", "/alerts"],
                ["Personnel", "/supervisor/personnel"],
                ["Audit Center", "/audit"],
                ["Evidence", "/evidence-upload"],
                ["Partners", "/partner-sources"],
            ],
        },
        supervisor: {
            title: "Supervisor Operations",
            greeting: `Team workload and case oversight for ${username}`,
            showBolos: true,
            showEvidence: true,
            actions: [
                ["Legal Order", "/legal-orders"],
                ["Alert", "/alerts"],
                ["Personnel", "/supervisor/personnel"],
                ["Audit Center", "/audit"],
                ["Evidence", "/evidence-upload"],
                ["Partners", "/partner-sources"],
            ],
        },
        investigator: {
            title: "Investigator Workspace",
            greeting: `Assigned cases and team activity for ${username}`,
            showBolos: true,
            showEvidence: true,
            actions: [
                ["Legal Order", "/legal-orders"],
                ["Alert", "/alerts"],
                ["Evidence", "/evidence-upload"],
            ],
        },
        analyst: {
            title: "Intelligence Workspace",
            greeting: `Analytical work queue for ${username}`,
            showBolos: true,
            showEvidence: true,
            actions: [
                ["Alert", "/alerts"],
                ["Evidence", "/evidence-upload"],
            ],
        },
        viewer: {
            title: "Beacon Workspace",
            greeting: `Authorized view for ${username}`,
            showBolos: false,
            showEvidence: false,
            actions: [],
        },
    };
    const profile = dashboardProfiles[role] || dashboardProfiles.viewer;

    // Refresh the dashboard summary so command-center data stays current while
    // the user keeps the page open.

    useEffect(() => {
        let isMounted = true;

        const loadSummary = async () => {
            if (!localStorage.getItem("token")) return;

            try {
                const data = await apiGet("/dashboard/summary");

                if (isMounted) {
                    setSummary(data);
                    setError("");
                }
            } catch (err) {
                console.error(err);

                if (isMounted) {
                    setError(
                        role === "supervisor"
                            ? ""
                            : err.message || "Could not load dashboard summary"
                    );
                }
            }
        };

        const timer = setTimeout(loadSummary, 0);
        const interval = setInterval(loadSummary, 10000);

        return () => {
            isMounted = false;
            clearTimeout(timer);
            clearInterval(interval);
        };
    }, [role]);

    useEffect(() => {
        if (!["admin", "agency_admin", "supervisor"].includes(role)) {
            return;
        }

        let isMounted = true;

        const loadSupervisorQueue = async () => {
            try {
                const data = await apiGet("/supervisor/queue");

                if (isMounted) {
                    setSupervisorQueue(data);
                }
            } catch (err) {
                console.error(err);

                if (isMounted) {
                    setSupervisorQueue(null);
                }
            }
        };

        loadSupervisorQueue();
        const interval = setInterval(loadSupervisorQueue, 30000);

        return () => {
            isMounted = false;
            clearInterval(interval);
        };
    }, [role]);

    useEffect(() => subscribeToReadState(() => {
        setReadStateVersion((current) => current + 1);
    }), []);

    useEffect(() => {
        const interval = setInterval(() => setCurrentTime(new Date()), 30000);
        return () => clearInterval(interval);
    }, []);

    const isCommandRole = ["admin", "agency_admin", "supervisor"].includes(role);
    const commandDashboard = supervisorQueue?.command_dashboard || {};
    const stallRiskSummary = supervisorQueue?.stall_risk_summary || {};
    const leadSummary = supervisorQueue?.lead_summary || {};
    const timelineSummary = supervisorQueue?.timeline_summary || {};
    const agencySummary = supervisorQueue?.agency_coordination || {};
    const totalLeadCount = Object.entries(leadSummary).reduce(
        (total, [key, value]) => key === "total" ? total : total + (Number(value) || 0),
        0
    );
    const metrics = [
        ["Cases", summary?.open_cases ?? commandDashboard.active_cases ?? 0, "/cases"],
        ["Alerts", summary?.new_alerts ?? commandDashboard.active_alerts ?? 0, "/alerts"],
        ["Leads", summary?.lead_count ?? summary?.leads ?? leadSummary.total ?? totalLeadCount, "/intelligence"],
        ["Evidence", summary?.total_evidence ?? summary?.evidence_uploaded_today ?? 0, "/evidence-upload"],
    ];
    const commandStatusGroups = [
        {
            label: "Case Load",
            items: [
                ["Active Cases", summary?.open_cases ?? commandDashboard.active_cases ?? 0, "/cases", "standard"],
                ["Critical Cases", summary?.critical_cases ?? 0, "/cases?priority=critical", "critical"],
                ["Missing Children", summary?.missing_children ?? 0, "/missing?age=minor", "attention"],
                ["AMBER Alerts", summary?.amber_alerts ?? 0, "/alerts?type=amber", "critical"],
                ["High Risk Cases", summary?.high_risk_cases ?? summary?.high_priority_cases ?? 0, "/missing?risk=high", "attention"],
            ],
        },
        {
            label: "Operational Workload",
            items: [
                ["Open Warrants", summary?.open_warrants ?? 0, "/legal-orders", "standard"],
                ["Outstanding Leads", summary?.outstanding_leads ?? leadSummary.total ?? totalLeadCount, "/intelligence", "standard"],
                ["Pending Evidence", summary?.pending_evidence ?? summary?.evidence_awaiting_review ?? 0, "/evidence-upload", "standard"],
            ],
        },
        {
            label: "Staffing",
            items: [
                ["Current Personnel", summary?.current_personnel ?? 0, "/supervisor/personnel", "personnel"],
            ],
        },
    ];
    const commandHeaderMetrics = [
        ["Personnel Online", summary?.current_personnel ?? 0, "/supervisor/personnel"],
        ["Active Investigations", summary?.open_cases ?? commandDashboard.active_cases ?? 0, "/cases"],
        ["Critical Incidents", summary?.critical_cases ?? 0, "/cases?priority=critical"],
        ["AMBER Alerts", summary?.amber_alerts ?? 0, "/alerts?type=amber"],
        ["Agency Requests", summary?.agency_requests ?? 0, "/partner-sources"],
    ];
    const commandQuickActions = [
        ["Create Search Warrant", "/legal-orders?template=judicial__search_warrant"],
        ["Send Interagency Request", "/legal-orders?template=interagency__investigative_assistance_request"],
        ["Issue BOLO", "/bolos?create=1"],
        ["Submit DNA", "/legal-orders?template=forensics__dna_submission"],
        ["Request Hospital Search", "/legal-orders?template=healthcare__hospital_admission_inquiry"],
        ["Launch AMBER Alert", "/alerts?create=amber"],
        ["Generate Briefing", "/command/briefing"],
        ["Open Intelligence Map", "/intelligence"],
    ];
    const workload = (supervisorQueue?.investigator_workload || []).length > 0
        ? supervisorQueue.investigator_workload.map((item) => [
            item.username,
            item.active_cases,
            item.workload_status,
            item.recent_results,
        ])
        : [];
    const actionRequiredItems = [
        {
            id: "high-risk-missing-persons",
            title: "High-risk missing person cases",
            count: summary?.high_priority_cases ?? commandDashboard.high_risk_missing_persons ?? 0,
            severity: "high",
            detail: "Confirm command attention and next investigative action.",
            path: "/missing?risk=high",
        },
        {
            id: "overdue-investigations",
            title: "Investigations at risk of stalling",
            count: summary?.stalled_cases ?? stallRiskSummary.inactive_7_days ?? 0,
            severity: "high",
            detail: "No recent activity, missing follow-up, or pending reports.",
            path: "/cases?filter=stalled",
        },
        {
            id: "unassigned-leads",
            title: "Unassigned leads",
            count: summary?.unassigned_leads ?? leadSummary.unassigned ?? 0,
            severity: "medium",
            detail: "Assign leads to investigators with available capacity.",
            path: "/intelligence",
        },
        {
            id: "unreviewed-evidence",
            title: "Unreviewed evidence",
            count: summary?.evidence_awaiting_review ?? 0,
            severity: "medium",
            detail: "Review lab returns, new uploads, and custody exceptions.",
            path: "/evidence-upload?status=overdue_review",
        },
        {
            id: "new-critical-sightings",
            title: "Critical sightings",
            count: summary?.critical_sightings ?? (timelineSummary.recent_sightings || []).length,
            severity: "high",
            detail: "Validate urgent sightings and decide whether to escalate.",
            path: "/sightings?filter=critical",
        },
        {
            id: "escalated-alerts",
            title: "Escalated alerts",
            count: summary?.new_alerts ?? 0,
            severity: "high",
            detail: "Review BOLOs, potential matches, and investigator escalations.",
            path: "/alerts",
        },
    ].map((item) => ({ ...item, count: getVisibleCount("tasks", item) }));
    const visibleActionItems = showAllActionItems ? actionRequiredItems : actionRequiredItems.slice(0, 4);
    const caseHealthItems = [
        ["Legal Orders", summary?.pending_legal_requests ?? summary?.pending_warrants ?? stallRiskSummary.pending_warrants ?? 0, "/legal-orders"],
        ["Missing reports", summary?.missing_reports ?? stallRiskSummary.missing_reports ?? 0, "/cases?filter=missing_reports"],
    ];
    const agencyCoordination = [
        ["Agencies involved", (agencySummary.involved_agencies || []).length || summary?.agency_requests || 0],
        ["Outstanding requests", agencySummary.outstanding_requests ?? summary?.outstanding_partner_requests ?? 0],
        ["Joint investigations", agencySummary.joint_investigations ?? summary?.joint_investigations ?? 0],
    ];
    const liveFeedEvents = [
        ...(summary?.recent_activity || [])
            .filter((item) => !String(item.details || "").toLowerCase().includes("deleted"))
            .map((item) => ({
                id: `activity-${item.id}`,
                timestamp: item.timestamp,
                title: item.details || String(item.action || "Agency activity").replaceAll("_", " "),
                detail: item.entity ? `Source: ${String(item.entity).replaceAll("_", " ")}` : "Agency activity",
            })),
        ...(timelineSummary.recent_events || []).map((event) => ({
            id: `timeline-${event.event_id}`,
            timestamp: event.timestamp,
            title: event.description || event.event_type || "Investigation updated",
            detail: event.case_number || event.location || `Case ${event.case_id}`,
        })),
        ...(timelineSummary.recent_sightings || []).map((sighting) => ({
            id: `sighting-${sighting.sighting_id}`,
            timestamp: sighting.created_at,
            title: sighting.location ? `Sighting reported at ${sighting.location}` : "New sighting reported",
            detail: sighting.case_number || `Case ${sighting.case_id}`,
            confidence: sighting.confidence_score,
        })),
        ...(timelineSummary.recent_evidence || []).map((item) => ({
            id: `evidence-${item.evidence_id}`,
            timestamp: item.created_at,
            title: `${item.evidence_type || "Evidence"} update`,
            detail: `${item.case_number || `Case ${item.case_id}`} · ${item.custody_status || "Collected"}`,
        })),
    ]
        .sort((a, b) => new Date(b.timestamp || 0) - new Date(a.timestamp || 0))
        .slice(0, 5);
    const exampleFeedEvents = [
        [2, "Houston PD accepted assistance request", "Interagency coordination"],
        [5, "Hospital uploaded unidentified patient", "Healthcare partner upload"],
        [11, "Lab completed DNA comparison", "Forensic result received"],
        [14, "Witness uploaded Ring footage", "Digital evidence received"],
        [19, "LPR camera hit", "White Ford F-150", 0.92],
    ].map(([minutesAgo, title, detail, confidence], index) => ({
        id: `example-feed-${index}`,
        timestamp: new Date(currentTime.getTime() - (minutesAgo * 60000)).toISOString(),
        title,
        detail,
        confidence,
    }));
    const liveIntelligenceFeed = liveFeedEvents.length > 0 ? liveFeedEvents : exampleFeedEvents;
    const formatFeedTime = (value) => {
        const date = new Date(value);
        return Number.isNaN(date.getTime())
            ? "Now"
            : date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
    };

    return (
        <div className="dashboard-page">
            {isCommandRole ? (
                <header className="command-operations-header">
                    <div className="command-operations-identity">
                        <span>Agency command view</span>
                        <h1>Command Operations Center</h1>
                        <div className="command-operations-clock" aria-label="Current local time">
                            <strong>{currentTime.toLocaleDateString(undefined, { weekday: "long" })}</strong>
                            <time dateTime={currentTime.toISOString()}>
                                {currentTime.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })}
                            </time>
                        </div>
                    </div>
                    <div className="command-operations-metrics" aria-label="Current command indicators">
                        {commandHeaderMetrics.map(([label, value, path]) => (
                            <Link key={label} to={path}>
                                <span>{label}</span>
                                <strong>{value}</strong>
                            </Link>
                        ))}
                    </div>
                </header>
            ) : (
                <div className="dashboard-header">
                    <h1>{profile.title}</h1>
                </div>
            )}

            {error && (
                <p className="alert-banner">
                    {error}
                </p>
            )}

            {(summary || error || role === "supervisor") && (
                <>
                    <div className="dashboard-board supervisor-command-dashboard">
                        {isCommandRole ? (
                            <section className="command-status-board" aria-labelledby="command-status-heading">
                                <div className="command-status-heading">
                                    <div>
                                        <span>Agency snapshot</span>
                                        <h2 id="command-status-heading">Command Status</h2>
                                    </div>
                                    <small>{summary ? "Live authorized agency view" : "Waiting for data"}</small>
                                </div>
                                <div className="command-status-groups">
                                    {commandStatusGroups.map((group) => (
                                        <div key={group.label} className={`command-status-group command-status-${group.label.toLowerCase().replaceAll(" ", "-")}`}>
                                            <h3>{group.label}</h3>
                                            <div className="command-status-metrics">
                                                {group.items.map(([label, value, path, tone]) => (
                                                    <Link key={label} to={path} className={`command-status-metric ${tone}`}>
                                                        <span>{label}</span>
                                                        <strong>{value ?? 0}</strong>
                                                    </Link>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </section>
                        ) : (
                            <div className="command-grid">
                                {metrics.map(([label, value, path]) => (
                                    <Link className="command-card" to={path} key={label}>
                                        <span>{label}</span>
                                        <strong>{value ?? 0}</strong>
                                        <small>{summary ? "Current authorized view" : "Waiting for data"}</small>
                                    </Link>
                                ))}
                            </div>
                        )}

                        {isCommandRole && (
                            <section className="dashboard-panel operations-map-panel">
                                <div className="dashboard-panel-header">
                                    <div>
                                        <span>Operations Map</span>
                                        <p>Agency-wide investigations, sightings, alerts, and partner activity.</p>
                                    </div>
                                    <Link to="/intelligence">Open Intelligence Map</Link>
                                </div>
                                <OperationsMap data={summary?.operations_map} />
                            </section>
                        )}

                        <div className="supervisor-home-grid">
                            <section className="dashboard-panel action-required-panel">
                                <div className="dashboard-panel-header">
                                    <span>Action Required Center</span>
                                    <Link to="/command/tasks">Open Tasks</Link>
                                </div>
                                <div className="action-required-list">
                                    {visibleActionItems.map((item) => (
                                        <article key={item.title} className={`action-required-item ${item.severity}`}>
                                            <div>
                                                <strong>{item.title}</strong>
                                                <p>{item.detail}</p>
                                            </div>
                                            <Link
                                                to={item.path}
                                                onClick={() => markItemViewed("tasks", item.id)}
                                                aria-label={`Open ${item.title}`}
                                            >
                                                {item.count}
                                            </Link>
                                        </article>
                                    ))}
                                </div>
                                {!showAllActionItems && (
                                    <button
                                        className="list-toggle-button"
                                        type="button"
                                        onClick={() => setShowAllActionItems(true)}
                                    >
                                        Show all action items
                                    </button>
                                )}
                            </section>

                            <section className="dashboard-panel command-health-panel">
                                <div className="dashboard-panel-header">
                                    <span>Case Health Monitoring</span>
                                    <div className="dashboard-panel-links">
                                        <Link to="/analytics">Analytics</Link>
                                        <Link to="/cases">Open Cases</Link>
                                    </div>
                                </div>
                                <div className="command-health-cases" aria-label="Case health monitoring">
                                    {caseHealthItems.map(([label, value, path]) => (
                                        <Link key={label} to={path} className="case-health-row">
                                            <span>{label}</span>
                                            <strong>{value}</strong>
                                        </Link>
                                    ))}
                                </div>
                            </section>

                            <section className="dashboard-panel workload-panel">
                                <div className="dashboard-panel-header">
                                    <span>Investigator Workload Analytics</span>
                                    <Link to="/supervisor/personnel">Personnel</Link>
                                </div>
                                {workload.length === 0 ? (
                                    <p>No investigator workload data available yet.</p>
                                ) : (
                                    workload.map(([name, count, status, recentResults]) => (
                                        <div
                                            key={name}
                                            className={`workload-row ${status || (
                                                count >= 12 ? "overloaded" : count <= 6 ? "available" : "balanced"
                                            )}`}
                                        >
                                            <span>{name}</span>
                                            <strong>{count} Cases</strong>
                                            {recentResults !== undefined && <small>{recentResults} recent actions</small>}
                                        </div>
                                    ))
                                )}
                            </section>

                            <section className="dashboard-panel unified-timeline-panel live-intelligence-feed">
                                <div className="dashboard-panel-header">
                                    <span>Live Intelligence Feed</span>
                                    <Link to="/cases">Review</Link>
                                </div>
                                <div className="live-intelligence-list">
                                {liveIntelligenceFeed.map((event) => (
                                    <article key={event.id} className="timeline-signal-row live-intelligence-row">
                                        <time dateTime={event.timestamp}>{formatFeedTime(event.timestamp)}</time>
                                        <div>
                                            <strong>{event.title}</strong>
                                            {event.detail && <p>{event.detail}</p>}
                                            {event.confidence !== undefined && event.confidence !== null && (
                                                <small>Confidence {Math.round(Number(event.confidence) * (Number(event.confidence) <= 1 ? 100 : 1))}%</small>
                                            )}
                                        </div>
                                    </article>
                                ))}
                                </div>
                            </section>

                            <section className="dashboard-panel agency-coordination-panel">
                                <div className="dashboard-panel-header">
                                    <span>Inter-Agency Coordination</span>
                                    <Link to="/supervisor/community">Review</Link>
                                </div>
                                {agencyCoordination.map(([label, value]) => (
                                    <div key={label} className="agency-coordination-row">
                                        <span>{label}</span>
                                        <strong>{value}</strong>
                                    </div>
                                ))}
                            </section>

                            <section className="dashboard-panel dashboard-actions-panel">
                                <div className="dashboard-panel-header">
                                    <span>Actions</span>
                                    <span>Quick start</span>
                                </div>
                                <h2>Command Actions</h2>
                                <div className="dashboard-action-list">
                                    {(isCommandRole ? commandQuickActions : profile.actions).map(([label, path]) => (
                                        <Link key={`${label}-${path}`} to={path}>
                                            {label}
                                        </Link>
                                    ))}
                                </div>
                            </section>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

export default Dashboard;
