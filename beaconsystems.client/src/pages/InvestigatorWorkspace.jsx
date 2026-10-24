import React, { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, apiPost } from "../api.jsx";
import { useVisiblePolling } from "../hooks/useVisiblePolling.js";

export default function InvestigatorWorkspace() {
    const [workspace, setWorkspace] = useState(null);
    const [error, setError] = useState("");
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [announcement, setAnnouncement] = useState("");
    const [markingNotificationId, setMarkingNotificationId] = useState(null);
    const loadWorkspace = useCallback(async (isActive = () => true) => {
        setIsRefreshing(true);
        try {
            const data = await apiGet("/dashboard/investigator");
            if (isActive()) {
                setWorkspace(data);
                setError("");
            }
        } catch (err) {
            if (isActive()) setError(err);
        } finally {
            if (isActive()) setIsRefreshing(false);
        }
    }, []);
    const markNotificationRead = async (notificationId) => {
        setMarkingNotificationId(notificationId);
        try {
            await apiPost(`/notifications/${notificationId}/read`, {});
            setWorkspace((current) => ({
                ...current,
                unread_notifications: current.unread_notifications.filter(
                    (item) => item.notification_id !== notificationId
                ),
            }));
            setAnnouncement("Notification marked read.");
        } catch (err) {
            setError(err);
        } finally {
            setMarkingNotificationId(null);
        }
    };
    useVisiblePolling(loadWorkspace, 30000);

    return <div className="beacon-page">
        <header className="beacon-page-header"><h1>Investigator Workspace</h1>
            <p>Your active assigned cases, urgent alerts, and case leads requiring review.</p>
            <nav aria-label="Investigator actions"><Link to="/cases">Browse authorized cases</Link>{" · "}
                <Link to="/evidence-upload">Upload evidence</Link>{" · "}
                <Link to="/alerts">Review alerts</Link>{" · "}
                <button type="button" onClick={() => loadWorkspace()} disabled={isRefreshing}>
                    {isRefreshing ? "Refreshing…" : "Refresh workspace"}
                </button></nav>
        </header>
        <p className="sr-only" role="status" aria-live="polite">{announcement}</p>
        {error && (
            <section className="workspace-state workspace-error-state" role="alert" aria-labelledby="workspace-error-heading">
                <h2 id="workspace-error-heading">{error.status === 403 ? "Workspace access unavailable" : "Workspace could not refresh"}</h2>
                <p>{error.message || error}{workspace && " Previously loaded work is shown below."}</p>
                {error.status !== 403 && (
                    <button type="button" onClick={() => loadWorkspace()} disabled={isRefreshing}>
                        {isRefreshing ? "Retrying…" : "Try again"}
                    </button>
                )}
            </section>
        )}
        {!workspace && !error && <div className="workspace-state" role="status" aria-live="polite"><span className="workspace-loading-indicator" aria-hidden="true" />Loading your work…</div>}
        {workspace && <div className="beacon-three-panel">
            <section className="beacon-panel" aria-labelledby="assigned-cases-heading"><h2 id="assigned-cases-heading">Assigned cases</h2>
                {workspace.assigned_cases.length === 0 && <p>No active cases are assigned to you.</p>}
                <ul>{workspace.assigned_cases.map((item) => <li key={item.case_id}>
                    <Link to={`/cases/${item.case_id}`}>{item.case_number}: {item.title}</Link>
                    <p>{item.priority || "Unspecified priority"} · {item.status || "Open"}</p>
                </li>)}</ul>
                {workspace.has_more.assigned_cases && <Link to="/cases">Browse more authorized cases</Link>}
            </section>
            <section className="beacon-panel" aria-labelledby="urgent-alerts-heading"><h2 id="urgent-alerts-heading">Urgent alerts</h2>
                {workspace.urgent_alerts.length === 0 && <p>No active high or critical alerts on your assigned cases.</p>}
                <ul>{workspace.urgent_alerts.map((item) => <li key={item.alert_id}>
                    <Link to={`/cases/${item.case_id}`}>{item.title || `Alert ${item.alert_id}`}</Link>
                    <p>{item.severity}</p>
                </li>)}</ul>
                {workspace.has_more.urgent_alerts && <Link to="/alerts">Review more alerts</Link>}
            </section>
            <section className="beacon-panel" aria-labelledby="pending-leads-heading"><h2 id="pending-leads-heading">Pending case leads</h2>
                <p>Oldest first. These leads belong to your assigned cases.</p>
                {workspace.pending_leads.length === 0 && <p>No pending leads on your assigned cases.</p>}
                <ul>{workspace.pending_leads.map((item) => <li key={item.lead_id}>
                    <Link to={`/cases/${item.case_id}`}>Lead {item.lead_id} · Case {item.case_id}</Link>
                    <p>{item.priority || "Normal priority"} · {item.status || "New"}{item.due_at ? ` · Due ${new Date(item.due_at).toLocaleString()}` : ""}</p>
                </li>)}</ul>
                {workspace.has_more.pending_leads && <Link to="/intelligence">Review more leads</Link>}
            </section>
            <section className="beacon-panel" aria-labelledby="unread-notifications-heading"><h2 id="unread-notifications-heading">Unread notifications</h2>
                {workspace.unread_notifications.length === 0 && <p>You are caught up.</p>}
                <ul>{workspace.unread_notifications.map((item) => <li key={item.notification_id}>
                    <Link to={item.case_id ? `/cases/${item.case_id}` : "/alerts"}>
                        {item.title}
                    </Link>
                    <p>{item.message}</p>
                    <button
                        type="button"
                        onClick={() => markNotificationRead(item.notification_id)}
                        disabled={markingNotificationId === item.notification_id}
                    >
                        {markingNotificationId === item.notification_id ? "Marking read…" : "Mark read"}
                    </button>
                </li>)}</ul>
                {workspace.has_more.unread_notifications && <Link to="/command/notifications">Review all notifications</Link>}
            </section>
        </div>}
    </div>;
}
