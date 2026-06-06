import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";



function Dashboard() {
    const [summary, setSummary] = useState(null);
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
                ["Case", "/cases"],
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
                ["Case", "/cases"],
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
                ["Case", "/cases"],
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
                ["Case", "/cases"],
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
                ["Case", "/cases"],
                ["Alert", "/alerts"],
                ["Evidence", "/evidence-upload"],
            ],
        },
        viewer: {
            title: "Beacon Workspace",
            greeting: `Authorized view for ${username}`,
            showBolos: false,
            showEvidence: false,
            actions: [
                ["Case", "/cases"],
            ],
        },
    };
    const profile = dashboardProfiles[role] || dashboardProfiles.viewer;

    // Refresh the dashboard summary so command-center data stays current while
    // the user keeps the page open.

    useEffect(() => {
        let isMounted = true;

        const loadSummary = async () => {
            const token = localStorage.getItem("token");

            if (!token) return;

            try {
                const response = await fetch("http://127.0.0.1:8000/dashboard/summary", {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });

                if (!response.ok) {
                    throw new Error("Failed to load dashboard summary");
                }

                const data = await response.json();

                if (isMounted) {
                    setSummary(data);
                    setError("");
                }
            } catch (err) {
                console.error(err);

                if (isMounted) {
                    setError("Could not load dashboard summary");
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
    }, []);

    const metrics = summary
        ? [
            ["Active Cases", summary.open_cases],
            ["High Priority", summary.high_priority_cases],
            ["New Alerts", summary.new_alerts],
            ["Evidence Today", summary.evidence_uploaded_today],
        ]
        : [];

    return (
        <div className="dashboard-page">
            <div className="dashboard-header">
                <h1>{profile.title}</h1>
                <p>{profile.greeting}</p>
            </div>

            {error && (
                <p className="alert-banner">
                    {error}
                </p>
            )}

            {(summary || error) && (
                <>
                    <div className="dashboard-board">
                        <div className="command-grid">
                            {(metrics.length > 0 ? metrics : [
                                ["Active Cases", 0],
                                ["High Priority", 0],
                                ["New Alerts", 0],
                                ["Evidence Today", 0],
                            ]).map(([label, value]) => (
                                <div className="command-card" key={label}>
                                    <span>{label}</span>
                                    <strong>{value ?? 0}</strong>
                                    <small>{summary ? "Current authorized view" : "Waiting for data"}</small>
                                </div>
                            ))}
                        </div>

                        <div className="dashboard-feature-grid">
                            <section className="dashboard-panel dashboard-panel-wide">
                                <div className="dashboard-panel-header">
                                    <span>Cases</span>
                                    <Link to="/cases">View all</Link>
                                </div>
                                <h2>Priority Work Queue</h2>
                            {!summary || summary.urgent_cases?.length === 0 ? (
                                <p>No high priority cases in your queue.</p>
                            ) : (
                                summary.urgent_cases?.slice(0, 2).map((caseItem) => (
                                    <article key={caseItem.case_id} className="queue-item">
                                        <div>
                                            <strong>{caseItem.case_number}</strong>
                                            <span>{caseItem.priority_level}</span>
                                        </div>
                                        <p>{caseItem.title}</p>
                                        <Link to={`/cases/${caseItem.case_id}`}>
                                            Open Case
                                        </Link>
                                    </article>
                                ))
                            )}
                            </section>

                            {/* Active BOLOs are surfaced on the dashboard for urgent field awareness. */}

                            {profile.showBolos && (
                            <section className="dashboard-panel">
                                <div className="dashboard-panel-header">
                                    <span>Field Awareness</span>
                                    <Link to="/alerts">Open</Link>
                                </div>
                                <h2>Active BOLOs</h2>

                            {!summary || summary.active_bolos?.length === 0 ? (
                                <p>No active BOLO alerts.</p>
                            ) : (
                                summary.active_bolos?.slice(0, 2).map((bolo) => (
                                    <article key={bolo.bolo_id} className="queue-item bolo-preview-item">
                                        <div>
                                            <strong>{bolo.title}</strong>
                                            <span>{bolo.risk_level}</span>
                                        </div>

                                        <p>{bolo.description}</p>

                                        <Link to="/alerts">Open Operational Alerts</Link>
                                    </article>
                                ))
                            )}
                            </section>
                            )}
                        
                            {profile.showEvidence && (
                            <section className="dashboard-panel">
                                <div className="dashboard-panel-header">
                                    <span>Evidence</span>
                                    <Link to="/evidence-upload">Open</Link>
                                </div>
                                <h2>Evidence Watch</h2>
                            {!summary || summary.recent_evidence?.length === 0 ? (
                                <p>No recent evidence uploads.</p>
                            ) : (
                                summary.recent_evidence?.slice(0, 2).map((item) => (
                                    <article key={item.evidence_id} className="queue-item">
                                        <div>
                                            <strong>{item.file_name || "Unnamed file"}</strong>
                                            <span>Case {item.case_id}</span>
                                        </div>
                                        <p>{item.description || "No description"}</p>
                                    </article>
                                ))
                            )}
                            </section>
                            )}

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
