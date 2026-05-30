import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";



function Dashboard() {
    const [summary, setSummary] = useState(null);
    const [error, setError] = useState(
        localStorage.getItem("token") ? "" : "No login token found. Please log in first."
    );
    const role = localStorage.getItem("role");

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
                <h1>Beacon Command Center</h1>
                <p>Operational overview, compliance watch, and urgent work queue.</p>
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
                                summary.urgent_cases?.map((caseItem) => (
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

                            <section className="dashboard-panel">
                                <div className="dashboard-panel-header">
                                    <span>Field Awareness</span>
                                    <Link to="/bolos">Open</Link>
                                </div>
                                <h2>Active BOLOs</h2>

                            {!summary || summary.active_bolos?.length === 0 ? (
                                <p>No active BOLO alerts.</p>
                            ) : (
                                summary.active_bolos?.map((bolo) => (
                                    <article key={bolo.bolo_id} className="queue-item bolo-preview-item">
                                        <div>
                                            <strong>{bolo.title}</strong>
                                            <span>{bolo.risk_level}</span>
                                        </div>

                                        <p>{bolo.description}</p>

                                        <Link to="/bolos">Open BOLO Board</Link>
                                    </article>
                                ))
                            )}
                            </section>
                        
                            <section className="dashboard-panel">
                                <div className="dashboard-panel-header">
                                    <span>Evidence</span>
                                    <Link to="/evidence">Open</Link>
                                </div>
                                <h2>Evidence Watch</h2>
                            {!summary || summary.recent_evidence?.length === 0 ? (
                                <p>No recent evidence uploads.</p>
                            ) : (
                                summary.recent_evidence?.map((item) => (
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

                       
                            <section className="dashboard-panel">
                                <div className="dashboard-panel-header">
                                    <span>Compliance</span>
                                    <Link to="/audit">Audit</Link>
                                </div>
                                <h2>Compliance Readiness</h2>
                                <div className="compliance-list">
                                    <span className="compliance-ok">Audit logging active</span>
                                    <span className="compliance-ok">Evidence chain of custody active</span>
                                    <span className="compliance-warning">
                                        Missing legal info: {summary?.missing_info_legal_requests ?? 0}
                                    </span>
                                    <span className="compliance-danger">
                                        Denied legal docs: {summary?.denied_legal_requests ?? 0}
                                    </span>
                                    <span className="compliance-pending">
                                        Legal docs pending review: {summary?.pending_legal_requests ?? 0}
                                    </span>
                                    <span className="compliance-ok">
                                        Approved legal docs: {summary?.approved_legal_requests ?? 0}
                                    </span>
                                    <span className="compliance-pending">
                                        Partner source approvals: {summary?.pending_partner_sources ?? 0}
                                    </span>
                                </div>
                            </section>

                            <section className="dashboard-panel dashboard-actions-panel">
                                <div className="dashboard-panel-header">
                                    <span>Actions</span>
                                    <span>Quick start</span>
                                </div>
                                <h2>Command Actions</h2>
                                <div className="dashboard-action-list">
                                    <Link to="/create-case">Create Case</Link>
                                    <Link to="/case-access">Request Case Access</Link>
                                    <Link to="/evidence-upload">Upload Evidence</Link>
                                    <Link to="/legal-access">Request Legal Access</Link>
                                    <Link to="/legal-orders">Request Legal Order</Link>
                                    <Link to="/bolos">Create BOLO</Link>
                                    {role === "admin" && (
                                        <Link to="/partner-sources">Add Partner Source</Link>
                                    )}
                                    <Link to="/partner-sources">Review Partner Data</Link>
                                    <Link to="/intelligence">Open Intelligence</Link>
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
