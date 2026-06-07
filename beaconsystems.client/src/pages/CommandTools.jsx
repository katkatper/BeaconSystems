import React from "react";
import { Link, useParams } from "react-router-dom";

const taskItems = [
    ["High-risk missing person cases", "Review active critical-risk cases and confirm command attention.", "High", "/cases"],
    ["Overdue investigations", "Check cases with no recent activity or missing follow-up documentation.", "High", "/supervisor/investigations"],
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
    const username = localStorage.getItem("username") || "Beacon User";
    const role = localStorage.getItem("role") || "viewer";
    const isTasks = tool === "tasks";
    const isNotifications = tool === "notifications";
    const isSettings = tool === "settings";
    const isProfile = tool === "profile";

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
                    {taskItems.map(([title, detail, priority, path]) => (
                        <article key={title} className="beacon-panel command-tool-card">
                            <div>
                                <span className={`task-priority ${priority.toLowerCase()}`}>
                                    {priority}
                                </span>
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
                        </article>
                    ))}
                </section>
            )}

            {isProfile && (
                <section className="beacon-panel profile-summary-panel">
                    <h2>{username}</h2>
                    <div className="beacon-status-list">
                        <span>Role: {role}</span>
                        <span>Agency ID: {localStorage.getItem("agency_id") || "Not set"}</span>
                        <span>Session: Active</span>
                    </div>
                </section>
            )}
        </div>
    );
}

export default CommandTools;
