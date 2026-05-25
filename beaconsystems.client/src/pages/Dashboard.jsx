import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";



function Dashboard() {
    const [summary, setSummary] = useState(null);
    const [error, setError] = useState(
        localStorage.getItem("token") ? "" : "No login token found. Please log in first."
    );

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
                    {summary.command_briefing && (
                        <section className="command-briefing">
                            <div>
                                <span>Urgent Case</span>
                                <strong>
                                    {summary.command_briefing.urgent_case
                                        ? summary.command_briefing.urgent_case.case_number
                                        : "None"}
                                </strong>
                                <p>
                                    {summary.command_briefing.urgent_case
                                        ? summary.command_briefing.urgent_case.title
                                        : "No urgent case in queue"}
                                </p>
                            </div>

                            <div>
                                <span>Latest Alert</span>

                                {/* Command Briefing highlights the highest-value operational items first. */}
                                <strong>
                                    {summary.command_briefing.latest_alert
                                        ? summary.command_briefing.latest_alert.title
                                        : "None"}
                                </strong>
                                <p>
                                    {summary.command_briefing.latest_alert
                                        ? summary.command_briefing.latest_alert.severity
                                        : "No recent alerts"}
                                </p>
                            </div>

                            <div>
                                <span>Latest Evidence</span>
                                <strong>
                                    {summary.command_briefing.latest_evidence
                                        ? summary.command_briefing.latest_evidence.file_name
                                        : "None"}
                                </strong>
                                <p>
                                    {summary.command_briefing.latest_evidence
                                        ? `Case ${summary.command_briefing.latest_evidence.case_id}`
                                        : "No recent evidence"}
                                </p>
                            </div>

                            <div>
                                <span>Compliance</span>
                                <strong>
                                    {summary.command_briefing.compliance.pending_legal_requests} pending
                                </strong>
                                <p>
                                    Legal requests awaiting review
                                </p>
                            </div>
                        </section>
                    )}
                    <section className="quick-actions">
                        <Link to="/create-case">Create Case</Link>
                        <Link to="/evidence-upload">Upload Evidence</Link>
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

                        {/* Active BOLOs are surfaced on the dashboard for urgent field awareness. */}

                        <section className="dashboard-panel">
                            <h2>Active BOLOs</h2>

                            {summary.active_bolos?.length === 0 ? (
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
