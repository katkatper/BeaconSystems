import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet } from "../api.jsx";
import SightingMap from "./SightingMap.jsx";



function Dashboard() {
    const [summary, setSummary] = useState(null);
    const [showAllActionItems, setShowAllActionItems] = useState(false);
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

    const metricLinks = {
        Cases: "/cases",
        Alerts: "/alerts",
        Leads: "/intelligence",
        Evidence: "/evidence-upload",
    };
    const metrics = summary
        ? [
            ["Cases", summary.open_cases],
            ["Alerts", summary.new_alerts],
            ["Leads", summary.external_records ?? 39],
            ["Evidence", summary.total_evidence ?? summary.evidence_uploaded_today],
        ]
        : [];
    const fallbackSightings = [
        {
            sighting_id: "demo-austin",
            case_id: "MP-2026-1024",
            location: "Austin, TX",
            description: "Recent field sighting under review.",
            latitude: 30.2672,
            longitude: -97.7431,
            confidence_score: 0.82,
            created_at: new Date().toISOString(),
        },
        {
            sighting_id: "demo-dallas",
            case_id: "MP-2026-1091",
            location: "Dallas, TX",
            description: "Potential hospital match.",
            latitude: 32.7767,
            longitude: -96.797,
            confidence_score: 0.95,
            created_at: new Date().toISOString(),
        },
    ];
    const criticalAlerts = [
        ["High Risk Missing Child", summary?.high_priority_cases ?? 0],
        ["Potential Hospital Match", summary?.external_matches ?? 1],
        ["Investigator Escalation", summary?.stalled_cases ?? 2],
        ["New Multi-Agency Request", summary?.agency_requests ?? 1],
    ];
    const workload = [
        ["Jones", 12],
        ["Smith", 5],
        ["Garcia", 15],
        ["Brown", 8],
    ];
    const actionRequiredItems = [
        {
            title: "High-risk missing person cases",
            count: summary?.high_priority_cases ?? 3,
            severity: "high",
            detail: "Confirm command attention and next investigative action.",
            path: "/missing?risk=high",
        },
        {
            title: "Investigations at risk of stalling",
            count: summary?.stalled_cases ?? 2,
            severity: "high",
            detail: "No recent activity, missing follow-up, or pending reports.",
            path: "/cases?filter=stalled",
        },
        {
            title: "Unassigned leads",
            count: summary?.unassigned_leads ?? 5,
            severity: "medium",
            detail: "Assign leads to investigators with available capacity.",
            path: "/intelligence",
        },
        {
            title: "Unreviewed evidence",
            count: summary?.evidence_awaiting_review ?? 4,
            severity: "medium",
            detail: "Review lab returns, new uploads, and custody exceptions.",
            path: "/evidence-upload?status=overdue_review",
        },
        {
            title: "Critical sightings",
            count: summary?.critical_sightings ?? 2,
            severity: "high",
            detail: "Validate urgent sightings and decide whether to escalate.",
            path: "/sightings?filter=critical",
        },
        {
            title: "Escalated alerts",
            count: summary?.new_alerts ?? 0,
            severity: "high",
            detail: "Review BOLOs, potential matches, and investigator escalations.",
            path: "/alerts",
        },
    ];
    const visibleActionItems = showAllActionItems ? actionRequiredItems : actionRequiredItems.slice(0, 4);
    const riskScore = Math.min(
        99,
        58
            + ((summary?.high_priority_cases ?? 3) * 6)
            + ((summary?.new_alerts ?? 0) * 2)
            + ((summary?.stalled_cases ?? 2) * 5)
    );
    const riskSignals = [
        ["Risk score", `${riskScore}`, "Weighted by case priority, stale activity, and alerts."],
        ["Case health", `${summary?.stalled_cases ?? 2} at risk`, "Stale activity, missing reports, or pending warrants."],
        ["Predictive alerts", `${summary?.predictive_alerts ?? 4}`, "Likely delays based on activity and workload patterns."],
    ];
    const caseHealthItems = [
        ["Inactive 7+ days", summary?.inactive_7_days ?? 6, "/cases?filter=stalled"],
        ["Pending warrants", summary?.pending_warrants ?? 2, "/legal-orders?status=pending"],
        ["Missing reports", summary?.missing_reports ?? 3, "/cases?filter=missing_reports"],
    ];
    const intelligenceItems = [
        ["External match", "Hospital, shelter, jail, and partner records consolidated."],
        ["Data match engine", "High-confidence matches routed to supervisor review."],
        ["Public tips", "New sightings and tips connected to active cases."],
    ];
    const agencyCoordination = [
        ["Agencies involved", summary?.agency_requests ?? 4],
        ["Outstanding requests", summary?.outstanding_partner_requests ?? 3],
        ["Joint investigations", summary?.joint_investigations ?? 2],
    ];
    const unifiedTimeline = [
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
                            {(metrics.length > 0 ? metrics : [
                                ["Cases", 248],
                                ["Alerts", 14],
                                ["Leads", 39],
                                ["Evidence", 1320],
                            ]).map(([label, value]) => (
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
                                            <Link to={item.path}>{item.count}</Link>
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

                            <section className="dashboard-panel risk-scoring-panel">
                                <div className="dashboard-panel-header">
                                    <span>Risk Scoring Engine</span>
                                    <Link to="/analytics">Analytics</Link>
                                </div>
                                <div className="risk-score-meter">
                                    <strong>{riskScore}</strong>
                                    <span>Command risk</span>
                                </div>
                                {riskSignals.slice(1).map(([label, value, detail]) => (
                                    <div key={label} className="risk-signal-row">
                                        <span>{label}</span>
                                        <strong>{value}</strong>
                                        <small>{detail}</small>
                                    </div>
                                ))}
                            </section>

                            <section className="dashboard-panel dashboard-panel-wide activity-map-panel">
                                <div className="dashboard-panel-header">
                                    <span>Geographic Activity Map</span>
                                    <Link to="/intelligence">Open Intelligence</Link>
                                </div>
                                <SightingMap sightings={summary?.recent_sightings || fallbackSightings} />
                                <div className="map-legend-row">
                                    <span>Sightings</span>
                                    <span>Cases</span>
                                    <span>Agencies</span>
                                    <span>Resource locations</span>
                                    <span>Heat maps</span>
                                </div>
                            </section>

                            <section className="dashboard-panel critical-alerts-panel">
                                <div className="dashboard-panel-header">
                                    <span>Critical Alerts</span>
                                    <Link to="/alerts">Open Alerts</Link>
                                </div>
                                {criticalAlerts.map(([label, value]) => (
                                    <article key={label} className="critical-alert-item">
                                        <strong>{label}</strong>
                                        <span>{value}</span>
                                    </article>
                                ))}
                            </section>

                            <section className="dashboard-panel case-health-panel">
                                <div className="dashboard-panel-header">
                                    <span>Case Health Monitoring</span>
                                    <Link to="/cases">Open Cases</Link>
                                </div>
                                {caseHealthItems.map(([label, value, path]) => (
                                    <Link key={label} to={path} className="case-health-row">
                                        <span>{label}</span>
                                        <strong>{value}</strong>
                                    </Link>
                                ))}
                            </section>

                            <section className="dashboard-panel workload-panel">
                                <div className="dashboard-panel-header">
                                    <span>Investigator Workload Analytics</span>
                                    <Link to="/supervisor/personnel">Personnel</Link>
                                </div>
                                {workload.map(([name, count]) => (
                                    <div
                                        key={name}
                                        className={`workload-row ${
                                            count >= 12 ? "overloaded" : count <= 6 ? "available" : "balanced"
                                        }`}
                                    >
                                        <span>{name}</span>
                                        <strong>{count} Cases</strong>
                                    </div>
                                ))}
                            </section>

                            <section className="dashboard-panel intelligence-feed-panel">
                                <div className="dashboard-panel-header">
                                    <span>Intelligence Feed</span>
                                    <Link to="/intelligence">Open Feed</Link>
                                </div>
                                {intelligenceItems.map(([label, detail]) => (
                                    <article key={label} className="intelligence-signal-item">
                                        <strong>{label}</strong>
                                        <p>{detail}</p>
                                    </article>
                                ))}
                            </section>

                            <section className="dashboard-panel agency-coordination-panel">
                                <div className="dashboard-panel-header">
                                    <span>Inter-Agency Coordination</span>
                                    <Link to="/partner-sources">Partners</Link>
                                </div>
                                {agencyCoordination.map(([label, value]) => (
                                    <div key={label} className="agency-coordination-row">
                                        <span>{label}</span>
                                        <strong>{value}</strong>
                                    </div>
                                ))}
                            </section>

                            <section className="dashboard-panel unified-timeline-panel">
                                <div className="dashboard-panel-header">
                                    <span>Unified Timeline Across Cases</span>
                                    <Link to="/cases">Review</Link>
                                </div>
                                {unifiedTimeline.map(([time, detail]) => (
                                    <article key={time} className="timeline-signal-row">
                                        <strong>{time}</strong>
                                        <p>{detail}</p>
                                    </article>
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
