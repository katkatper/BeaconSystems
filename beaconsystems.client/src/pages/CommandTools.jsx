import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiGet, apiPost } from "../api.jsx";

const taskItems = [
    ["High-risk missing person cases", "Review active critical-risk cases and confirm command attention.", "High", "/missing?risk=high"],
    ["Overdue investigations", "Check cases with no recent activity or missing follow-up documentation.", "High", "/cases?filter=stalled"],
    ["Unassigned leads", "Assign new leads to investigators with available capacity.", "Medium", "/intelligence"],
    ["Unreviewed evidence", "Review new evidence, lab returns, and custody exceptions.", "Medium", "/evidence-upload"],
    ["New critical sightings", "Validate urgent sightings and decide whether to escalate alerts.", "High", "/sightings"],
    ["Escalated alerts", "Review BOLOs, potential matches, and investigator escalations.", "High", "/alerts"],
];

const notificationItems = [
    ["Potential hospital match", "External record match is ready for supervisor review.", "/intelligence"],
    ["New BOLO activity", "An operational alert was created for field coordination.", "/alerts"],
    ["Evidence custody update", "A custody event was recorded on an active case.", "/evidence-upload"],
    ["Agency request received", "A partner agency submitted a new information request.", "/agencies"],
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
    const username = localStorage.getItem("username") || "Beacon User";
    const role = localStorage.getItem("role") || "viewer";
    const isTasks = tool === "tasks";
    const isNotifications = tool === "notifications";
    const isSettings = tool === "settings";
    const isProfile = tool === "profile";
    const liveTaskItems = [
        [taskItems[0][0], taskItems[0][1], taskItems[0][2], taskItems[0][3], summary?.high_priority_cases ?? 0],
        [taskItems[1][0], taskItems[1][1], taskItems[1][2], taskItems[1][3], summary?.stalled_cases ?? 0],
        [taskItems[2][0], taskItems[2][1], taskItems[2][2], taskItems[2][3], summary?.unassigned_cases ?? 0],
        [taskItems[3][0], taskItems[3][1], taskItems[3][2], taskItems[3][3], summary?.evidence_awaiting_review ?? 0],
        [taskItems[4][0], taskItems[4][1], taskItems[4][2], taskItems[4][3], summary?.critical_sightings ?? 0],
        [taskItems[5][0], taskItems[5][1], taskItems[5][2], taskItems[5][3], summary?.new_alerts ?? 0],
    ];

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
                    {liveTaskItems.map(([title, detail, priority, path, count]) => (
                        <article key={title} className="beacon-panel command-tool-card">
                            <div>
                                <span className={`task-priority ${priority.toLowerCase()}`}>
                                    {priority}
                                </span>
                                <span className="task-count">{count}</span>
                                <h2>{title}</h2>
                            </div>
                            <p>{detail}</p>
                            <Link to={path}>Open</Link>
                        </article>
                    ))}
                </section>
            )}

            {isNotifications && (
                <section className="command-tool-grid">
                    {notificationItems.map(([title, detail, path]) => (
                        <article key={title} className="beacon-panel command-tool-card">
                            <h2>{title}</h2>
                            <p>{detail}</p>
                            <Link to={path}>Review</Link>
                        </article>
                    ))}
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
                                    <strong>{mfaSetup.secret}</strong>
                                    <small>{mfaSetup.otpauth_uri}</small>
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
                </div>
            )}
        </div>
    );
}

export default CommandTools;
