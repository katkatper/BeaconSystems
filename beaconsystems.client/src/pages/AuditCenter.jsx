import React, { useEffect, useState } from "react";

function AuditCenter() {
    const [search, setSearch] = useState("");
    const [users, setUsers] = useState([]);
    const [selectedUser, setSelectedUser] = useState(null);
    const [audit, setAudit] = useState(null);
    const [message, setMessage] = useState("");

    const token = localStorage.getItem("token");

    // Audit search starts with users, then drills into one person's full trail.
    // This keeps supervisors focused and avoids showing every log by default.
    useEffect(() => {
        let isMounted = true;

        const loadUsers = async () => {
            try {
                const response = await fetch(
                    `http://127.0.0.1:8000/audit/users?q=${encodeURIComponent(search)}&limit=5`,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );

                if (!response.ok) {
                    throw new Error("Could not load audit users");
                }

                const data = await response.json();

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
    }, [search, token]);

    const loadUserActivity = async (user) => {
        setSelectedUser(user);
        setAudit(null);
        setMessage("");

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/audit/users/${user.user_id}/activity`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                throw new Error("Could not load user activity");
            }

            const data = await response.json();
            setAudit(data);
        } catch (err) {
            console.error(err);
            setMessage("Could not load user audit activity.");
        }
    };

    const displayName = (user) => {
        return user?.username || user?.email || `User ${user?.user_id || "Unknown"}`;
    };

    return (
        <div className="audit-page">
            <div className="audit-header">
                <h1>Audit & Compliance Center</h1>
                <p>Search a user and review their access, evidence, and operational activity.</p>
            </div>

            {message && <p className="alert-banner">{message}</p>}

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
                            users.map((user) => (
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

            {/* User activity panels stay hidden until a supervisor selects a user. */}
            {selectedUser && audit && (
                <div className="audit-grid">
                    <section className="audit-panel">
                        <h2>Recent Activity</h2>

                        {(audit.recent_activity || []).length === 0 ? (
                            <p>No recent activity found for this user.</p>
                        ) : (
                            (audit.recent_activity || []).map((item) => (
                                <article key={item.log_id} className="queue-item">
                                    <div>
                                        <strong>{item.action}</strong>
                                        <span>{item.entity}</span>
                                    </div>
                                    <p>{item.details || "No details provided"}</p>
                                </article>
                            ))
                        )}
                    </section>

                    <section className="audit-panel">
                        <h2>Restricted Case Access</h2>

                        {(audit.restricted_case_access || []).length === 0 ? (
                            <p>No restricted case access found for this user.</p>
                        ) : (
                            (audit.restricted_case_access || []).map((item) => (
                                <article key={item.grant_id} className="queue-item">
                                    <div>
                                        <strong>Case {item.case_id}</strong>
                                        <span>{item.status}</span>
                                    </div>
                                    <p>{item.reason}</p>
                                </article>
                            ))
                        )}
                    </section>

                    <section className="audit-panel">
                        <h2>Evidence Chain Events</h2>

                        {(audit.evidence_chain_events || []).length === 0 ? (
                            <p>No evidence events found for this user.</p>
                        ) : (
                            (audit.evidence_chain_events || []).map((item) => (
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
                    </section>
                </div>
            )}
        </div>
    );
}

export default AuditCenter;
