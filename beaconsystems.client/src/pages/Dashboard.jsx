import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

function Dashboard() {
    const [summary, setSummary] = useState(null);
    const [error, setError] = useState(
        localStorage.getItem("token") ? "" : "No login token found. Please log in first."
    );

    const loadSummary = async () => {
        const token = localStorage.getItem("token");

        if (!token) return;

        const response = await fetch("http://127.0.0.1:8000/dashboard/summary", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            throw new Error("Failed to load dashboard summary");
        }

        const data = await response.json();
        setSummary(data);
    };

    useEffect(() => {
        loadSummary().catch((err) => {
            console.error(err);
            setError("Could not load dashboard summary");
        });

        const interval = setInterval(() => {
            loadSummary().catch((err) => console.error(err));
        }, 10000);

        return () => clearInterval(interval);
    }, []);

    const metrics = summary
        ? [
              ["Active Cases", summary.open_cases],
              ["High Priority", summary.high_priority_cases],
              ["New Alerts", summary.new_alerts],
              ["Pending Legal", summary.pending_legal_requests],
              ["Pending Partners", summary.pending_partner_sources],
              ["Evidence Today", summary.evidence_uploaded_today],
              ["Restricted Access", summary.restricted_access_events],
              ["Active Sources", summary.active_partner_sources],
          ]
        : [];

    return (
        <div className="dashboard-page">
            <div className="dashboard-header">
                <h1>Beacon Command Center</h1>
                <p>Operational overview, compliance watch, and urgent work queue.</p>
            </div>

            {error && <p>{error}</p>}

            {summary && (
                <>
                    <div className="command-grid">
                        {metrics.map(([label, value]) => (
                            <div className="command-card" key={label}>
                                <h3>{label}</h3>
                                <p>{value ?? 0}</p>
                            </div>
                        ))}
                    </div>

                    <section className="quick-actions">
                        <Link to="/create-case">Create Case</Link>
                        <Link to="/case-access">Request Case Access</Link>
                        <Link to="/evidence-upload">Upload Evidence</Link>
                        <Link to="/legal-access">Submit Legal Access</Link>
                        <Link to="/partner-sources">Add Partner Source</Link>
                        <Link to="/intelligence">Open Intelligence</Link>
                    </section>

                    <div className="dashboard-columns">
                        <section className="dashboard-panel">
                            <h2>Priority Work Queue</h2>
                            {summary.urgent_cases?.length === 0 ? (
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

                        <section className="dashboard-panel">
                            <h2>Recent Alerts</h2>
                            {summary.recent_alerts?.length === 0 ? (
                                <p>No recent alerts.</p>
                            ) : (
                                summary.recent_alerts?.map((alert) => (
                                    <article key={alert.alert_id} className="queue-item">
                                        <div>
                                            <strong>{alert.title}</strong>
                                            <span>{alert.severity}</span>
                                        </div>
                                        <p>{alert.description}</p>
                                    </article>
                                ))
                            )}
                        </section>

                        <section className="dashboard-panel">
                            <h2>Live Intelligence Snapshot</h2>
                            {summary.recent_sightings?.length === 0 ? (
                                <p>No recent sightings.</p>
                            ) : (
                                summary.recent_sightings?.map((sighting) => (
                                    <article
                                        key={sighting.sighting_id}
                                        className="queue-item"
                                    >
                                        <div>
                                            <strong>{sighting.location || "Unknown location"}</strong>
                                            <span>
                                                {sighting.confidence_score ?? "unknown"}
                                            </span>
                                        </div>
                                        <p>{sighting.description || "No description"}</p>
                                    </article>
                                ))
                            )}
                        </section>

                        <section className="dashboard-panel">
                            <h2>Evidence Watch</h2>
                            {summary.recent_evidence?.length === 0 ? (
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
                            <h2>Case Access Audit</h2>
                            {summary.recent_access?.length === 0 ? (
                                <p>No recent restricted access events.</p>
                            ) : (
                                summary.recent_access?.map((access) => (
                                    <article key={access.grant_id} className="queue-item">
                                        <div>
                                            <strong>Case {access.case_id}</strong>
                                            <span>User {access.user_id}</span>
                                        </div>
                                        <p>{access.reason}</p>
                                    </article>
                                ))
                            )}
                        </section>

                        <section className="dashboard-panel">
                            <h2>Compliance Readiness</h2>
                            <div className="compliance-list">
                                <span>Audit logging active</span>
                                <span>Evidence chain of custody active</span>
                                <span>Legal access review queue active</span>
                                <span>Partner source approval queue active</span>
                                <span>Restricted case access logging active</span>
                            </div>
                        </section>
                    </div>
                </>
            )}
        </div>
    );
}

export default Dashboard;
