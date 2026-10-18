import React, { useState } from "react";
import { Link } from "react-router-dom";
import { apiGet } from "../api.jsx";
import { useVisiblePolling } from "../hooks/useVisiblePolling.js";

export default function InvestigatorWorkspace() {
    const [workspace, setWorkspace] = useState(null);
    const [error, setError] = useState("");
    useVisiblePolling(async (isActive) => {
        try {
            const data = await apiGet("/dashboard/investigator");
            if (isActive()) { setWorkspace(data); setError(""); }
        } catch (err) { if (isActive()) setError(err.message); }
    }, 30000);

    return <div className="beacon-page">
        <header className="beacon-page-header"><h1>Investigator Workspace</h1>
            <p>Your active assigned cases, urgent alerts, and case leads requiring review.</p>
            <nav aria-label="Investigator actions"><Link to="/cases">Browse authorized cases</Link>{" · "}
                <Link to="/evidence-upload">Upload evidence</Link>{" · "}
                <Link to="/alerts">Review alerts</Link></nav>
        </header>
        {error && <p role="alert">Could not refresh your work: {error}{workspace && " Previously loaded work is shown below."}</p>}
        {!workspace && !error && <p role="status">Loading your work…</p>}
        {workspace && <div className="beacon-three-panel">
            <section className="beacon-panel"><h2>Assigned cases</h2>
                {workspace.assigned_cases.length === 0 && <p>No active cases are assigned to you.</p>}
                <ul>{workspace.assigned_cases.map((item) => <li key={item.case_id}>
                    <Link to={`/cases/${item.case_id}`}>{item.case_number}: {item.title}</Link>
                    <p>{item.priority || "Unspecified priority"} · {item.status || "Open"}</p>
                </li>)}</ul>
                {workspace.has_more.assigned_cases && <Link to="/cases">Browse more authorized cases</Link>}
            </section>
            <section className="beacon-panel"><h2>Urgent alerts</h2>
                {workspace.urgent_alerts.length === 0 && <p>No active high or critical alerts on your assigned cases.</p>}
                <ul>{workspace.urgent_alerts.map((item) => <li key={item.alert_id}>
                    <Link to={`/cases/${item.case_id}`}>{item.title || `Alert ${item.alert_id}`}</Link>
                    <p>{item.severity}</p>
                </li>)}</ul>
                {workspace.has_more.urgent_alerts && <Link to="/alerts">Review more alerts</Link>}
            </section>
            <section className="beacon-panel"><h2>Pending case leads</h2>
                <p>Oldest first. These leads belong to your assigned cases.</p>
                {workspace.pending_leads.length === 0 && <p>No pending leads on your assigned cases.</p>}
                <ul>{workspace.pending_leads.map((item) => <li key={item.lead_id}>
                    <Link to={`/cases/${item.case_id}`}>Lead {item.lead_id} · Case {item.case_id}</Link>
                    <p>{item.status || "New"}</p>
                </li>)}</ul>
                {workspace.has_more.pending_leads && <Link to="/intelligence">Review more leads</Link>}
            </section>
        </div>}
    </div>;
}
