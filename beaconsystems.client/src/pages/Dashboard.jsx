import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet } from "../api.jsx";
import { getVisibleCount, markItemViewed, subscribeToReadState } from "../commandCenterState.js";



function Dashboard() {
    const [summary, setSummary] = useState(null);
    const [supervisorQueue, setSupervisorQueue] = useState(null);
    const [showAllActionItems, setShowAllActionItems] = useState(false);
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

    const metricLinks = {
        Cases: "/cases",
        Alerts: "/alerts",
        Leads: "/intelligence",
        Evidence: "/evidence-upload",
    };
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
        ["Cases", summary?.open_cases ?? commandDashboard.active_cases ?? 0],
        ["Alerts", summary?.new_alerts ?? commandDashboard.active_alerts ?? 0],
        ["Leads", summary?.lead_count ?? summary?.leads ?? leadSummary.total ?? totalLeadCount],
        ["Evidence", summary?.total_evidence ?? summary?.evidence_uploaded_today ?? 0],
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
    const highPriorityCount = summary?.high_priority_cases ?? commandDashboard.high_risk_missing_persons ?? 0;
    const activeAlertCount = summary?.new_alerts ?? commandDashboard.active_alerts ?? 0;
    const stalledCaseCount = summary?.stalled_cases ?? stallRiskSummary.inactive_7_days ?? 0;
    const predictiveAlertCount = summary?.predictive_alerts ?? 0;
    const riskScore = Math.min(
        99,
        18
            + (highPriorityCount * 7)
            + (activeAlertCount * 3)
            + (stalledCaseCount * 5)
            + predictiveAlertCount
    );
    const riskSignals = [
        ["Case health", `${stalledCaseCount} at risk`],
        ["Predictive alerts", `${predictiveAlertCount}`],
    ];
    const caseHealthItems = [
        ["Inactive 7+ days", summary?.inactive_7_days ?? stallRiskSummary.inactive_7_days ?? 0, "/cases?filter=stalled"],
        ["Pending warrants", summary?.pending_warrants ?? stallRiskSummary.pending_warrants ?? 0, "/legal-orders?status=pending"],
        ["Missing reports", summary?.missing_reports ?? stallRiskSummary.missing_reports ?? 0, "/cases?filter=missing_reports"],
    ];
    const agencyCoordination = [
        ["Agencies involved", (agencySummary.involved_agencies || []).length || summary?.agency_requests || 0],
        ["Outstanding requests", agencySummary.outstanding_requests ?? summary?.outstanding_partner_requests ?? 0],
        ["Joint investigations", agencySummary.joint_investigations ?? summary?.joint_investigations ?? 0],
    ];
    const recentTimelineEvents = [
        ...(timelineSummary.recent_events || []).map((event) => [
            event.case_number || `Case ${event.case_id}`,
            event.description || event.event_type || event.location || "Timeline event recorded.",
        ]),
        ...(timelineSummary.recent_sightings || []).map((sighting) => [
            sighting.case_number || `Case ${sighting.case_id}`,
            `Sighting reported${sighting.location ? ` at ${sighting.location}` : ""}.`,
        ]),
        ...(timelineSummary.recent_evidence || []).map((item) => [
            item.case_number || `Case ${item.case_id}`,
            `${item.evidence_type || "Evidence"} recorded as ${item.custody_status || "collected"}.`,
        ]),
    ];
    const unifiedTimeline = recentTimelineEvents.length > 0
        ? recentTimelineEvents.slice(0, 3)
        : [
            ["Today", "Critical sighting and supervisor alert review."],
            ["Yesterday", "Evidence submitted and external intelligence received."],
            ["This week", "Investigator actions, lead assignments, and agency requests."],
        ];

    return (
        <div className="dashboard-page">
            <div className="dashboard-header">
                <h1>{profile.title}</h1>
            </div>

            {error && (
                <p className="alert-banner">
                    {error}
                </p>
            )}

            {(summary || error || role === "supervisor") && (
                <>
                    <div className="dashboard-board supervisor-command-dashboard">
                        <div className="command-grid">
                            {metrics.map(([label, value]) => (
                                <Link className="command-card" to={metricLinks[label] || "/"} key={label}>
                                    <span>{label}</span>
                                    <strong>{value ?? 0}</strong>
                                    <small>{summary ? "Current authorized view" : "Waiting for data"}</small>
                                </Link>
                            ))}
                        </div>

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
                                    <span>Command Risk &amp; Case Health</span>
                                    <div className="dashboard-panel-links">
                                        <Link to="/analytics">Analytics</Link>
                                        <Link to="/cases">Open Cases</Link>
                                    </div>
                                </div>
                                <div className="command-health-summary">
                                    <div className="risk-score-meter">
                                        <strong>{riskScore}</strong>
                                        <span>Command risk</span>
                                    </div>
                                    <div className="command-health-signals">
                                        {riskSignals.map(([label, value]) => (
                                            <div key={label} className="risk-signal-row">
                                                <span>{label}</span>
                                                <strong>{value}</strong>
                                            </div>
                                        ))}
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

                            <section className="dashboard-panel unified-timeline-panel">
                                <div className="dashboard-panel-header">
                                    <span>Unified Timeline Across Cases</span>
                                    <Link to="/cases">Review</Link>
                                </div>
                                {unifiedTimeline.map(([time, detail], index) => (
                                    <article key={`${time}-${index}`} className="timeline-signal-row">
                                        <strong>{time}</strong>
                                        <p>{detail}</p>
                                    </article>
                                ))}
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
                                    {profile.actions.map(([label, path]) => (
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
