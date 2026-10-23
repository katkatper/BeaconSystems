import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiGet, apiPost } from "../api.jsx";
import { getVisibleCount, markItemViewed, subscribeToReadState } from "../commandCenterState.js";

const taskItems = [
    ["high-risk-missing-persons", "High-risk missing person cases", "Review active critical-risk cases and confirm command attention.", "High", "/missing?risk=high"],
    ["overdue-investigations", "Overdue investigations", "Check cases with no recent activity or missing follow-up documentation.", "High", "/cases?filter=stalled"],
    ["unassigned-leads", "Unassigned leads", "Assign new leads to investigators with available capacity.", "Medium", "/intelligence"],
    ["unreviewed-evidence", "Unreviewed evidence", "Review new evidence, lab returns, and custody exceptions.", "Medium", "/evidence-upload"],
    ["new-critical-sightings", "New critical sightings", "Validate urgent sightings and decide whether to escalate alerts.", "High", "/sightings"],
    ["escalated-alerts", "Escalated alerts", "Review BOLOs, potential matches, and investigator escalations.", "High", "/alerts"],
];

const settingsItems = [
    ["Account settings", "Review your Beacon profile, role, and notification preferences."],
    ["Workspace defaults", "Set preferred landing views for supervisor workflows."],
    ["Security", "Review session handling and password rotation status."],
    ["Notification rules", "Choose which alerts should appear in command notifications."],
];

function CommandTools() {
    const { tool = "tasks" } = useParams();
    const [summary, setSummary] = useState(null);
    const [mfaSetup, setMfaSetup] = useState(null);
    const [mfaCode, setMfaCode] = useState("");
    const [mfaMessage, setMfaMessage] = useState("");
    const [sessions, setSessions] = useState([]);
    const [sessionMessage, setSessionMessage] = useState("");
    const [notifications, setNotifications] = useState([]);
    const [notificationMessage, setNotificationMessage] = useState("");
    const [, setReadStateVersion] = useState(0);
    const username = localStorage.getItem("username") || "Beacon User";
    const role = localStorage.getItem("role") || "viewer";
    const isTasks = tool === "tasks";
    const isNotifications = tool === "notifications";
    const isSettings = tool === "settings";
    const isProfile = tool === "profile";
    const liveTaskItems = [
        { id: taskItems[0][0], title: taskItems[0][1], detail: taskItems[0][2], priority: taskItems[0][3], path: taskItems[0][4], count: summary?.high_priority_cases ?? 0 },
        { id: taskItems[1][0], title: taskItems[1][1], detail: taskItems[1][2], priority: taskItems[1][3], path: taskItems[1][4], count: summary?.stalled_cases ?? 0 },
        { id: taskItems[2][0], title: taskItems[2][1], detail: taskItems[2][2], priority: taskItems[2][3], path: taskItems[2][4], count: summary?.unassigned_cases ?? 0 },
        { id: taskItems[3][0], title: taskItems[3][1], detail: taskItems[3][2], priority: taskItems[3][3], path: taskItems[3][4], count: summary?.evidence_awaiting_review ?? 0 },
        { id: taskItems[4][0], title: taskItems[4][1], detail: taskItems[4][2], priority: taskItems[4][3], path: taskItems[4][4], count: summary?.critical_sightings ?? 0 },
        { id: taskItems[5][0], title: taskItems[5][1], detail: taskItems[5][2], priority: taskItems[5][3], path: taskItems[5][4], count: summary?.new_alerts ?? 0 },
    ].map((item) => ({ ...item, count: getVisibleCount("tasks", item) }));
    useEffect(() => {
        let isMounted = true;

        const loadSummary = async () => {
            try {
                const data = await apiGet("/dashboard/summary");

                if (isMounted) {
                    setSummary(data);
                }
            } catch (err) {
                console.error(err);
            }
        };

        loadSummary();

        return () => {
            isMounted = false;
        };
    }, []);

    useEffect(() => subscribeToReadState(() => {
        setReadStateVersion((current) => current + 1);
    }), []);

    useEffect(() => {
        if (!isNotifications) return undefined;
        let isMounted = true;
        apiGet("/notifications/?limit=100")
            .then((data) => { if (isMounted) setNotifications(data); })
            .catch((err) => { if (isMounted) setNotificationMessage(err.message); });
        return () => { isMounted = false; };
    }, [isNotifications]);

    const readNotification = async (item) => {
        try {
            const updated = await apiPost(`/notifications/${item.notification_id}/read`, {});
            setNotifications((current) => current.map((entry) =>
                entry.notification_id === item.notification_id ? updated : entry
            ));
        } catch (err) {
            setNotificationMessage(err.message);
        }
    };

    const readAllNotifications = async () => {
        try {
            const result = await apiPost("/notifications/read-all", {});
            const readAt = result.read_at || new Date().toISOString();
            setNotifications((current) => current.map((item) => ({ ...item, read_at: item.read_at || readAt })));
            setNotificationMessage(`${result.read_count} notification(s) marked read.`);
        } catch (err) {
            setNotificationMessage(err.message);
        }
    };

    const loadSessions = async () => {
        try {
            setSessions(await apiGet("/users/sessions"));
        } catch (err) {
            console.error(err);
            setSessionMessage("Could not load active sessions.");
        }
    };

    useEffect(() => {
        if (!isProfile) return undefined;
        let isMounted = true;
        apiGet("/users/sessions")
            .then((data) => {
                if (isMounted) setSessions(data);
            })
            .catch((err) => {
                console.error(err);
                if (isMounted) setSessionMessage("Could not load active sessions.");
            });
        return () => {
            isMounted = false;
        };
    }, [isProfile]);

    const revokeSession = async (sessionId, isCurrent) => {
        try {
            await apiPost(`/users/sessions/${sessionId}/revoke`, {});
            if (isCurrent) {
                localStorage.clear();
                window.location.assign("/login");
                return;
            }
            setSessionMessage("Session revoked.");
            await loadSessions();
        } catch (err) {
            setSessionMessage(err.message || "Could not revoke session.");
        }
    };

    const revokeOtherSessions = async () => {
        try {
            const result = await apiPost("/users/sessions/revoke-others", {});
            setSessionMessage(`${result.revoked_count} other session(s) revoked.`);
            await loadSessions();
        } catch (err) {
            setSessionMessage(err.message || "Could not revoke other sessions.");
        }
    };

    const startMfaSetup = async () => {
        setMfaMessage("");

        try {
            const data = await apiGet("/users/mfa/setup");
            setMfaSetup(data);
        } catch (err) {
            console.error(err);
            setMfaMessage("Could not start MFA setup.");
        }
    };

    const enableMfa = async (event) => {
        event.preventDefault();
        setMfaMessage("");

        try {
            await apiPost("/users/mfa/enable", { code: mfaCode });
            setMfaCode("");
            setMfaMessage("MFA is now enabled for this account.");
            setMfaSetup((current) => current ? { ...current, enabled: true } : current);
        } catch (err) {
            console.error(err);
            setMfaMessage(err.message || "Could not enable MFA.");
        }
    };

    const disableMfa = async (event) => {
        event.preventDefault();
        setMfaMessage("");

        try {
            await apiPost("/users/mfa/disable", { code: mfaCode });
            setMfaCode("");
            setMfaSetup(null);
            setMfaMessage("MFA has been disabled for this account.");
        } catch (err) {
            console.error(err);
            setMfaMessage(err.message || "Could not disable MFA.");
        }
    };

    return (
        <div className="command-tools-page beacon-page">
            <section className="beacon-page-header">
                <h1>
                    {isTasks && "Action Required Center"}
                    {isNotifications && "Notifications"}
                    {isSettings && "Settings"}
                    {isProfile && "User Profile"}
                </h1>
            </section>

            {isTasks && (
                <section className="command-tool-grid">
                    {liveTaskItems.map(({ id, title, detail, priority, path, count }) => (
                        <article key={title} className="beacon-panel command-tool-card">
                            <div>
                                <span className={`task-priority ${priority.toLowerCase()}`}>
                                    {priority}
                                </span>
                                <span className="task-count">{count}</span>
                                <h2>{title}</h2>
                            </div>
                            <p>{detail}</p>
                            <Link to={path} onClick={() => markItemViewed("tasks", id)}>
                                Open
                            </Link>
                        </article>
                    ))}
                </section>
            )}

            {isNotifications && (
                <section>
                    <div className="command-notification-actions">
                        <p>{notifications.filter((item) => !item.read_at).length} unread</p>
                        <button type="button" onClick={readAllNotifications}>Mark all read</button>
                    </div>
                    {notificationMessage && <p role="status">{notificationMessage}</p>}
                    {notifications.length === 0 && <p>You have no notifications.</p>}
                    <div className="command-tool-grid">
                        {notifications.map((item) => (
                            <article key={item.notification_id} className={`beacon-panel command-tool-card ${item.read_at ? "notification-read" : "notification-unread"}`}>
                                <div>
                                    <span className="task-count">{item.read_at ? "Read" : "New"}</span>
                                    <h2>{item.title}</h2>
                                </div>
                                <p>{item.message}</p>
                                <Link to={item.case_id ? `/cases/${item.case_id}` : "/alerts"} onClick={() => readNotification(item)}>
                                    Review
                                </Link>
                                {!item.read_at && <button type="button" onClick={() => readNotification(item)}>Mark read</button>}
                            </article>
                        ))}
                    </div>
                </section>
            )}

            {isSettings && (
                <section className="command-tool-grid">
                    {settingsItems.map(([title, detail]) => (
                        <article key={title} className="beacon-panel command-tool-card">
                            <h2>{title}</h2>
                            <p>{detail}</p>
                            {title === "Security" && (
                                <div className="session-status-list">
                                    <span>Idle timeout: 30 minutes</span>
                                    <span>Absolute session: backend token expiration</span>
                                </div>
                            )}
                        </article>
                    ))}
                </section>
            )}

            {isProfile && (
                <div className="profile-security-layout">
                    <section className="beacon-panel profile-summary-panel">
                        <h2>{username}</h2>
                        <div className="beacon-status-list">
                            <span>Role: {role}</span>
                            <span>Agency ID: {localStorage.getItem("agency_id") || "Not set"}</span>
                            <span>Session: Active</span>
                        </div>
                    </section>

                    <section className="beacon-panel mfa-setup-panel">
                        <div className="audit-panel-heading">
                            <span>Security</span>
                            <strong>Multi-Factor Authentication</strong>
                        </div>

                        <p>
                            Protect this Beacon account with a six-digit authenticator code at sign-in.
                        </p>

                        {!mfaSetup ? (
                            <button type="button" onClick={startMfaSetup}>
                                Set Up MFA
                            </button>
                        ) : (
                            <>
                                <div className="mfa-secret-box">
                                    <span>Issuer: {mfaSetup.issuer}</span>
                                    <span>Account: {mfaSetup.account}</span>
                                    {mfaSetup.enabled ? (
                                        <strong>MFA is enabled. The enrollment secret is hidden.</strong>
                                    ) : (
                                        <>
                                            <strong>{mfaSetup.secret}</strong>
                                            <small>{mfaSetup.otpauth_uri}</small>
                                        </>
                                    )}
                                </div>

                                <form onSubmit={mfaSetup.enabled ? disableMfa : enableMfa}>
                                    <input
                                        type="text"
                                        inputMode="numeric"
                                        value={mfaCode}
                                        onChange={(event) => setMfaCode(event.target.value)}
                                        placeholder="Authenticator code"
                                    />
                                    <button type="submit">
                                        {mfaSetup.enabled ? "Disable MFA" : "Enable MFA"}
                                    </button>
                                </form>
                            </>
                        )}

                        {mfaMessage && <p className="login-message">{mfaMessage}</p>}
                    </section>

                    <section className="beacon-panel mfa-setup-panel">
                        <div className="audit-panel-heading">
                            <span>Security</span>
                            <strong>Active Sessions</strong>
                        </div>
                        <p>Review devices signed in to your Beacon account.</p>
                        <div className="session-status-list">
                            {sessions.map((item) => (
                                <span key={item.session_id}>
                                    <strong>{item.is_current ? "Current session" : "Other session"}</strong>
                                    {item.ip_address || "Unknown address"} · {new Date(item.last_seen_at).toLocaleString()}
                                    <button type="button" onClick={() => revokeSession(item.session_id, item.is_current)}>
                                        Revoke
                                    </button>
                                </span>
                            ))}
                        </div>
                        {sessions.length > 1 && (
                            <button type="button" onClick={revokeOtherSessions}>Revoke Other Sessions</button>
                        )}
                        {sessionMessage && <p className="login-message">{sessionMessage}</p>}
                    </section>
                </div>
            )}
        </div>
    );
}

export default CommandTools;
