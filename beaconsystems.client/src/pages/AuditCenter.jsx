import React, { useEffect, useState } from "react";
import { apiGet } from "../api.jsx";

function AuditCenter() {
    const [search, setSearch] = useState("");
    const [users, setUsers] = useState([]);
    const [selectedUser, setSelectedUser] = useState(null);
    const [audit, setAudit] = useState(null);
    const [summary, setSummary] = useState(null);
    const [securityPosture, setSecurityPosture] = useState(null);
    const [showMoreUsers, setShowMoreUsers] = useState(false);
    const [expandedAuditLists, setExpandedAuditLists] = useState({});
    const [message, setMessage] = useState("");

    // Audit search starts with users, then drills into one person's full trail.
    // This keeps supervisors focused and avoids showing every log by default.
    useEffect(() => {
        let isMounted = true;

        const loadSummary = async () => {
            try {
                const data = await apiGet("/audit/summary");

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

    useEffect(() => {
        let isMounted = true;

        const loadSecurityPosture = async () => {
            try {
                const data = await apiGet("/security/posture");

                if (isMounted) {
                    setSecurityPosture(data);
                }
            } catch (err) {
                console.error(err);
            }
        };

        loadSecurityPosture();

        return () => {
            isMounted = false;
        };
    }, []);

    useEffect(() => {
        let isMounted = true;

        const loadUsers = async () => {
            try {
                const data = await apiGet(`/audit/users?q=${encodeURIComponent(search)}&limit=5`);

                if (isMounted) {
                    setUsers(Array.isArray(data) ? data : []);
                    setMessage("");
                }
            } catch (err) {
                console.error(err);

                if (isMounted) {
                    setMessage("Could not search audit users. Admin or agency admin access is required.");
                }
            }
        };

        const timer = setTimeout(loadUsers, 250);

        return () => {
            isMounted = false;
            clearTimeout(timer);
        };
    }, [search]);

    const loadUserActivity = async (user) => {
        setSelectedUser(user);
        setAudit(null);
        setMessage("");

        try {
            const data = await apiGet(`/audit/users/${user.user_id}/activity`);
            setAudit(data);
        } catch (err) {
            console.error(err);
            setMessage("Could not load user audit activity.");
        }
    };

    const displayName = (user) => {
        return user?.username || user?.email || `User ${user?.user_id || "Unknown"}`;
    };
    const visibleAuditItems = (key, items) =>
        (items || []).slice(0, expandedAuditLists[key] ? 6 : 2);
    const renderAuditToggle = (key, count, label) => count > 2 ? (
        <button
            type="button"
            className="list-toggle-button"
            onClick={() =>
                setExpandedAuditLists((current) => ({
                    ...current,
                    [key]: !current[key],
                }))
            }
        >
            {expandedAuditLists[key] ? "Show fewer" : `Show ${Math.min(4, count - 2)} more ${label}`}
        </button>
    ) : null;

    return (
        <div className="audit-page">
            <div className="audit-header">
                <h1>Audit & Compliance Center</h1>
            </div>

            {message && <p className="alert-banner">{message}</p>}

            <section className="audit-panel security-posture-panel">
                <div className="audit-panel-heading">
                    <span>Security Dashboard</span>
                    <strong>Secure Data-Sharing Posture</strong>
                </div>

                <div className="security-control-grid">
                    {(securityPosture?.controls || []).map((control) => (
                        <article
                            key={control.key}
                            className={`security-control-card ${control.status}`}
                        >
                            <div>
                                <strong>{control.label}</strong>
                                <span>{control.status === "active" ? "Active" : "Needs attention"}</span>
                            </div>
                            <p>{control.summary}</p>
                            {control.roles && (
                                <small>Roles: {control.roles.join(", ")}</small>
                            )}
                            {control.key_id && (
                                <small>Key ID: {control.key_id}</small>
                            )}
                        </article>
                    ))}
                </div>

                <div className="security-transparency-row">
                    <span>
                        Audit events
                        <strong>{securityPosture?.transparency?.audit_events_total ?? 0}</strong>
                    </span>
                    <span>
                        Evidence custody events
                        <strong>{securityPosture?.transparency?.evidence_chain_events ?? 0}</strong>
                    </span>
                    <span>
                        Partner approvals pending
                        <strong>{securityPosture?.transparency?.pending_partner_approvals ?? 0}</strong>
                    </span>
                    <span>
                        Restricted access pending
                        <strong>{securityPosture?.transparency?.restricted_access_pending ?? 0}</strong>
                    </span>
                </div>
            </section>

            <div className="audit-search-layout">
                <section className="audit-panel">
                    <h2>User Search</h2>

                    <input
                        value={search}
                        onChange={(event) => setSearch(event.target.value)}
                        placeholder="Search by name, username, or email"
                    />

                    <div className="audit-user-list">
                        {users.length === 0 ? (
                            <p>No users found.</p>
                        ) : (
                            users.slice(0, showMoreUsers ? 6 : 2).map((user) => (
                                <button
                                    key={user.user_id}
                                    type="button"
                                    className={`audit-user-button ${selectedUser?.user_id === user.user_id ? "active" : ""
                                        }`}
                                    onClick={() => loadUserActivity(user)}
                                >
                                    <strong>{displayName(user)}</strong>
                                    <span>{user.role}</span>
                                    <small>{user.email || user.username}</small>
                                </button>
                            ))
                        )}
                        {users.length > 2 && (
                            <button
                                type="button"
                                className="list-toggle-button"
                                onClick={() => setShowMoreUsers((current) => !current)}
                            >
                                {showMoreUsers ? "Show fewer" : `Show ${Math.min(4, users.length - 2)} more users`}
                            </button>
                        )}
                    </div>
                </section>

                <section className="audit-panel audit-user-summary">
                    <h2>Selected User</h2>

                    {selectedUser ? (
                        <>
                            <strong>{displayName(selectedUser)}</strong>
                            <p>{selectedUser.email || "No email on file"}</p>
                            <small>
                                Role: {selectedUser.role} | User ID: {selectedUser.user_id}
                            </small>
                        </>
                    ) : (
                        <p>Select a user to view audit activity.</p>
                    )}
                </section>
            </div>

            <section className="audit-panel audit-readiness-panel">
                <div className="audit-panel-heading">
                    <span>Compliance</span>
                    <strong>Compliance Readiness</strong>
                </div>

                <div className="compliance-list">
                    <span className="compliance-ok">
                        Audit logging {summary?.compliance_readiness?.audit_logging_active ? "active" : "not active"}
                    </span>
                    <span className="compliance-ok">
                        Evidence chain of custody {summary?.compliance_readiness?.evidence_chain_active ? "active" : "not active"}
                    </span>
                    <span className="compliance-warning">
                        Missing legal info: {summary?.compliance_readiness?.missing_info_legal_requests ?? 0}
                    </span>
                    <span className="compliance-danger">
                        Denied legal docs: {summary?.compliance_readiness?.denied_legal_requests ?? 0}
                    </span>
                    <span className="compliance-pending">
                        Legal docs pending review: {summary?.compliance_readiness?.pending_legal_requests ?? 0}
                    </span>
                    <span className="compliance-ok">
                        Approved legal docs: {summary?.compliance_readiness?.approved_legal_requests ?? 0}
                    </span>
                    <span className="compliance-pending">
                        Partner source approvals: {summary?.compliance_readiness?.pending_partner_sources ?? 0}
                    </span>
                </div>
            </section>

            {/* User activity panels stay hidden until a supervisor selects a user. */}
            {selectedUser && audit && (
                <div className="audit-grid">
                    <section className="audit-panel">
                        <h2>Recent Activity</h2>

                        {(audit.recent_activity || []).length === 0 ? (
                            <p>No recent activity found for this user.</p>
                        ) : (
                            visibleAuditItems("recentActivity", audit.recent_activity).map((item) => (
                                <article key={item.log_id} className="queue-item">
                                    <div>
                                        <strong>{item.action}</strong>
                                        <span>{item.entity}</span>
                                    </div>
                                    <p>{item.details || "No details provided"}</p>
                                </article>
                            ))
                        )}
                        {renderAuditToggle("recentActivity", (audit.recent_activity || []).length, "events")}
                    </section>

                    <section className="audit-panel">
                        <h2>Restricted Case Access</h2>

                        {(audit.restricted_case_access || []).length === 0 ? (
                            <p>No restricted case access found for this user.</p>
                        ) : (
                            visibleAuditItems("restrictedCaseAccess", audit.restricted_case_access).map((item) => (
                                <article key={item.grant_id} className="queue-item">
                                    <div>
                                        <strong>Case {item.case_id}</strong>
                                        <span>{item.status}</span>
                                    </div>
                                    <p>{item.reason}</p>
                                </article>
                            ))
                        )}
                        {renderAuditToggle("restrictedCaseAccess", (audit.restricted_case_access || []).length, "entries")}
                    </section>

                    <section className="audit-panel">
                        <h2>Evidence Chain Events</h2>

                        {(audit.evidence_chain_events || []).length === 0 ? (
                            <p>No evidence events found for this user.</p>
                        ) : (
                            visibleAuditItems("evidenceChainEvents", audit.evidence_chain_events).map((item) => (
                                <article key={item.chain_id} className="queue-item">
                                    <div>
                                        <strong>{item.action}</strong>
                                        <span>Case {item.case_id}</span>
                                    </div>
                                    <p>{item.details || "No details provided"}</p>
                                    <small>Evidence {item.evidence_id}</small>
                                </article>
                            ))
                        )}
                        {renderAuditToggle("evidenceChainEvents", (audit.evidence_chain_events || []).length, "events")}
                    </section>
                </div>
            )}
        </div>
    );
}

export default AuditCenter;
