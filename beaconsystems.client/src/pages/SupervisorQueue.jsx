import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";


// SupervisorQueue gives agency leadership one place to review items that need
// oversight before action: legal access, partner integrations, restricted case
// access, high-priority cases, and active BOLO alerts.

function SupervisorQueue() {
    const [queue, setQueue] = useState(null);
    const [message, setMessage] = useState("");
    const [reviewNotes, setReviewNotes] = useState({});
    const [activeWorkspace, setActiveWorkspace] = useState("access");
    const [users, setUsers] = useState([]);
    const [resetPasswords, setResetPasswords] = useState({});
    const [newUser, setNewUser] = useState({
        username: "",
        email: "",
        password: "",
        role: "investigator",
        agency_id: "",
    });
    const [teamForm, setTeamForm] = useState({
        case_id: "",
        user_id: "",
        role: "support_investigator",
        reason: "",
    });
    const [exchanges, setExchanges] = useState([]);
    const [exchangeForm, setExchangeForm] = useState({
        case_id: "",
        from_agency: "",
        to_agency: "",
        information_type: "investigative lead",
        legal_authority: "",
        reason: "",
        summary: "",
    });

    const token = localStorage.getItem("token");

    const getApiErrorMessage = (errorData, fallback) => {
        if (Array.isArray(errorData.detail)) {
            return errorData.detail
                .map((item) => `${item.loc?.slice(1).join(".") || "field"}: ${item.msg}`)
                .join("; ");
        }

        return errorData.detail || fallback;
    };

    const workspaceCards = [
        ["access", "Access", "Review pending legal/case access and restricted access activity."],
        ["users", "Users", "Register users, disable accounts, and manage team access."],
        ["case-teams", "Case Teams", "Assign the lead investigator and assemble the investigative team."],
        ["court-docs", "Court Documents", "Track warrants, subpoenas, court orders, and legal authority."],
        ["bolos", "BOLO", "Create and monitor BOLO alerts for field awareness."],
    ];


 // Load the review queue once when the page opens. The backend enforces that
// only admins and agency admins can access this endpoint.

    useEffect(() => {

 // Prevent React from updating state if the user leaves the page before the
        // request finishes.

        let isMounted = true;

        // The token proves the user is logged in; role checks happen on the API.

        const loadQueue = async () => {
            try {
                const response = await fetch("http://127.0.0.1:8000/supervisor/queue", {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });

                if (!response.ok) {
                    throw new Error("Could not load supervisor queue");
                }

                const data = await response.json();

                if (isMounted) {
                    setQueue(data);
                    setMessage("");
                }
            } catch (err) {
                console.error(err);

                if (isMounted) {
                    setMessage("Could not load supervisor queue. Admin or agency admin access is required.");
                }
            }
        };

        loadQueue();

        return () => {
            isMounted = false;
        };
    }, [token]);

    useEffect(() => {
        let isMounted = true;

        const loadUsers = async () => {
            try {
                const response = await fetch("http://127.0.0.1:8000/admin/users/", {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });

                if (!response.ok) {
                    throw new Error("Could not load users");
                }

                const data = await response.json();

                if (isMounted) {
                    setUsers(Array.isArray(data) ? data : []);
                }
            } catch (err) {
                console.error(err);
            }
        };

        const timer = setTimeout(loadUsers, 0);

        return () => {
            isMounted = false;
            clearTimeout(timer);
        };
    }, [token]);

    useEffect(() => {
        let isMounted = true;

        const loadExchanges = async () => {
            try {
                const response = await fetch("http://127.0.0.1:8000/agency-exchanges/", {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });

                if (!response.ok) {
                    throw new Error("Could not load agency exchanges");
                }

                const data = await response.json();

                if (isMounted) {
                    setExchanges(Array.isArray(data) ? data : []);
                }
            } catch (err) {
                console.error(err);
            }
        };

        loadExchanges();

        return () => {
            isMounted = false;
        };
    }, [token]);

    const reviewCaseAccess = async (grantId, action) => {
        try {
            const response = await fetch(
                `http://127.0.0.1:8000/supervisor/case-access/${grantId}/${action}`,
                {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({
                        review_notes: reviewNotes[grantId] || "",
                    }),
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Could not review case access request");
            }

            const data = await response.json();
            setMessage(data.message);

            setQueue((currentQueue) => {
                if (!currentQueue) {
                    return currentQueue;
                }

                return {
                    ...currentQueue,
                    pending_case_access: (currentQueue.pending_case_access || []).filter(
                        (item) => item.grant_id !== grantId
                    ),
                };
            });

            setReviewNotes((currentNotes) => {
                const nextNotes = { ...currentNotes };
                delete nextNotes[grantId];
                return nextNotes;
            });
        } catch (err) {
            console.error(err);
            setMessage(err.message || "Could not review case access request.");
        }
    };

    const registerUser = async (event) => {
        event.preventDefault();

        try {
            const payload = {
                username: newUser.username.trim(),
                email: newUser.email.trim(),
                password: newUser.password,
                role: newUser.role,
                agency_id: newUser.agency_id ? Number(newUser.agency_id) : null,
            };

            const response = await fetch("http://127.0.0.1:8000/admin/users/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(
                    getApiErrorMessage(errorData, "Could not register user")
                );
            }

            const data = await response.json();
            setMessage(`${data.username} was registered as ${data.role}.`);
            setUsers((currentUsers) => [...currentUsers, data].sort((a, b) =>
                (a.username || "").localeCompare(b.username || "")
            ));
            setNewUser({
                username: "",
                email: "",
                password: "",
                role: "investigator",
                agency_id: "",
            });
        } catch (err) {
            console.error(err);
            setMessage(err.message || "Could not register user.");
        }
    };

    const updateUserStatus = async (userId, isActive) => {
        try {
            const response = await fetch(
                `http://127.0.0.1:8000/admin/users/${userId}/status?is_active=${isActive}`,
                {
                    method: "PUT",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Could not update user status");
            }

            setUsers((currentUsers) =>
                currentUsers.map((user) =>
                    user.user_id === userId ? { ...user, is_active: isActive } : user
                )
            );
            setMessage(isActive ? "User reactivated." : "User disabled and archived from active work.");
        } catch (err) {
            console.error(err);
            setMessage(err.message || "Could not update user status.");
        }
    };

    const resetUserPassword = async (userId) => {
        const temporaryPassword = resetPasswords[userId] || "";

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/admin/users/${userId}/reset-password`,
                {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({
                        temporary_password: temporaryPassword,
                    }),
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(
                    getApiErrorMessage(errorData, "Could not reset user password")
                );
            }

            const data = await response.json();
            setResetPasswords((currentPasswords) => ({
                ...currentPasswords,
                [userId]: "",
            }));
            setMessage(`${data.message}. They must change it on next login.`);
        } catch (err) {
            console.error(err);
            setMessage(err.message || "Could not reset user password.");
        }
    };

    const handleExchangeChange = (event) => {
        setExchangeForm({
            ...exchangeForm,
            [event.target.name]: event.target.value,
        });
    };

    const handleTeamChange = (event) => {
        setTeamForm({
            ...teamForm,
            [event.target.name]: event.target.value,
        });
    };

    const assignCaseTeamMember = async (event) => {
        event.preventDefault();

        try {
            const payload = {
                user_id: Number(teamForm.user_id),
                role: teamForm.role,
                reason: teamForm.reason,
            };

            const response = await fetch(
                `http://127.0.0.1:8000/supervisor/cases/${Number(teamForm.case_id)}/team`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify(payload),
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Could not assign case team member");
            }

            setMessage("Case team member assigned and logged.");
            setTeamForm({
                case_id: "",
                user_id: "",
                role: "support_investigator",
                reason: "",
            });
        } catch (err) {
            console.error(err);
            setMessage(err.message || "Could not assign case team member.");
        }
    };

    const submitExchange = async (event) => {
        event.preventDefault();

        try {
            const payload = {
                ...exchangeForm,
                case_id: Number(exchangeForm.case_id),
            };

            const response = await fetch("http://127.0.0.1:8000/agency-exchanges/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Could not record agency exchange");
            }

            setMessage("Agency information exchange recorded and audited.");
            setExchangeForm({
                case_id: "",
                from_agency: "",
                to_agency: "",
                information_type: "investigative lead",
                legal_authority: "",
                reason: "",
                summary: "",
            });

            const refreshResponse = await fetch("http://127.0.0.1:8000/agency-exchanges/", {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });
            const refreshData = refreshResponse.ok ? await refreshResponse.json() : [];
            setExchanges(Array.isArray(refreshData) ? refreshData : []);
        } catch (err) {
            console.error(err);
            setMessage(err.message || "Could not record agency exchange.");
        }
    };



    return (
        <div className="supervisor-page">
            <div className="supervisor-header">
                <h1>Supervisor Workspace</h1>
            </div>

            <section className="supervisor-admin-links" aria-label="Supervisor administration links">
                {workspaceCards.map(([key, title, description]) => (
                    <button
                        key={key}
                        type="button"
                        className={`supervisor-admin-card ${activeWorkspace === key ? "active" : ""}`}
                        onClick={() => setActiveWorkspace(key)}
                    >
                        <strong>{title}</strong>
                        <small>{description}</small>
                    </button>
                ))}
            </section>

            {activeWorkspace === "users" && (
            <div className="supervisor-operations-grid">
                <section className="supervisor-user-registration">
                    <div className="supervisor-panel-header">
                        <span>User Access</span>
                        <strong>Register New User</strong>
                    </div>

                    <form className="supervisor-user-form" onSubmit={registerUser}>
                        <input
                            type="text"
                            placeholder="Username"
                            value={newUser.username}
                            onChange={(event) =>
                                setNewUser((current) => ({ ...current, username: event.target.value }))
                            }
                            required
                        />

                        <input
                            type="email"
                            placeholder="Email"
                            value={newUser.email}
                            onChange={(event) =>
                                setNewUser((current) => ({ ...current, email: event.target.value }))
                            }
                            required
                        />

                        <input
                            type="password"
                            placeholder="Temporary password"
                            value={newUser.password}
                            onChange={(event) =>
                                setNewUser((current) => ({ ...current, password: event.target.value }))
                            }
                            required
                        />

                        <select
                            value={newUser.role}
                            onChange={(event) =>
                                setNewUser((current) => ({ ...current, role: event.target.value }))
                            }
                        >
                            <option value="investigator">Investigator</option>
                            <option value="supervisor">Supervisor</option>
                            <option value="analyst">Analyst</option>
                            <option value="viewer">Viewer</option>
                            <option value="agency_admin">Agency Admin</option>
                            <option value="admin">Admin</option>
                        </select>

                        <input
                            type="number"
                            min="1"
                            placeholder="Agency ID"
                            value={newUser.agency_id}
                            onChange={(event) =>
                                setNewUser((current) => ({ ...current, agency_id: event.target.value }))
                            }
                        />

                        <button type="submit">Register User</button>
                    </form>
                </section>

                <section className="supervisor-user-registration">
                    <div className="supervisor-panel-header">
                        <span>User Access</span>
                        <strong>Disable or Restore Users</strong>
                    </div>

                    <div className="supervisor-user-list">
                        {users.length === 0 ? (
                            <p>No users found for your agency.</p>
                        ) : (
                            users.map((user) => (
                                <article key={user.user_id} className="queue-item">
                                    <div>
                                        <strong>{user.username}</strong>
                                        <span>{user.is_active ? "active" : "disabled"}</span>
                                    </div>
                                    <p>{user.email}</p>
                                    <p>{user.role} | Agency {user.agency_id || "Unassigned"}</p>
                                    <button
                                        type="button"
                                        onClick={() => updateUserStatus(user.user_id, !user.is_active)}
                                    >
                                        {user.is_active ? "Disable / Archive" : "Restore User"}
                                    </button>
                                    <div className="supervisor-password-reset">
                                        <input
                                            type="password"
                                            placeholder="New temporary password"
                                            value={resetPasswords[user.user_id] || ""}
                                            onChange={(event) =>
                                                setResetPasswords((currentPasswords) => ({
                                                    ...currentPasswords,
                                                    [user.user_id]: event.target.value,
                                                }))
                                            }
                                        />
                                        <button
                                            type="button"
                                            onClick={() => resetUserPassword(user.user_id)}
                                        >
                                            Reset Password
                                        </button>
                                    </div>
                                </article>
                            ))
                        )}
                    </div>
                </section>
            </div>
            )}

            {activeWorkspace === "case-teams" && (
            <div className="supervisor-operations-grid">
                <section className="agency-exchange-panel supervisor-exchange-panel">
                    <div className="agency-exchange-header">
                        <span>Information Sharing</span>
                        <strong>Agency Exchange Log</strong>
                    </div>

                    <form className="agency-exchange-form" onSubmit={submitExchange}>
                        <input
                            type="number"
                            name="case_id"
                            min="1"
                            placeholder="Case ID"
                            value={exchangeForm.case_id}
                            onChange={handleExchangeChange}
                            required
                        />

                        <input
                            name="from_agency"
                            placeholder="From agency"
                            value={exchangeForm.from_agency}
                            onChange={handleExchangeChange}
                            required
                        />

                        <input
                            name="to_agency"
                            placeholder="To agency"
                            value={exchangeForm.to_agency}
                            onChange={handleExchangeChange}
                            required
                        />

                        <input
                            name="information_type"
                            placeholder="Information type"
                            value={exchangeForm.information_type}
                            onChange={handleExchangeChange}
                            required
                        />

                        <input
                            name="legal_authority"
                            placeholder="Legal authority or agreement"
                            value={exchangeForm.legal_authority}
                            onChange={handleExchangeChange}
                        />

                        <textarea
                            name="reason"
                            placeholder="Why this exchange is approved"
                            value={exchangeForm.reason}
                            onChange={handleExchangeChange}
                            required
                        />

                        <textarea
                            name="summary"
                            placeholder="Information exchanged"
                            value={exchangeForm.summary}
                            onChange={handleExchangeChange}
                            required
                        />

                        <button type="submit">Record Approved Exchange</button>
                    </form>

                    <div className="agency-exchange-list">
                        {exchanges.length === 0 ? (
                            <p>No agency exchanges recorded yet.</p>
                        ) : (
                            exchanges.slice(0, 5).map((exchange) => (
                                <article key={exchange.exchange_id} className="agency-exchange-card">
                                    <div>
                                        <strong>{exchange.from_agency} to {exchange.to_agency}</strong>
                                        <span>Case {exchange.case_id}</span>
                                    </div>
                                    <p>{exchange.summary}</p>
                                    <p>Reason: {exchange.reason}</p>
                                    <small>
                                        Approved by user {exchange.approved_by} | {exchange.status}
                                    </small>
                                </article>
                            ))
                        )}
                    </div>
                </section>

                <section className="case-team-panel">
                    <div className="supervisor-panel-header">
                        <span>Case Team</span>
                        <strong>Assemble Case Team</strong>
                    </div>

                    <p className="supervisor-panel-note">
                        Assign the lead investigator on the case record first, then add support
                        investigators, analysts, or supervisor observers as needed.
                    </p>

                    <form className="case-team-form" onSubmit={assignCaseTeamMember}>
                        <input
                            type="number"
                            name="case_id"
                            min="1"
                            placeholder="Case ID"
                            value={teamForm.case_id}
                            onChange={handleTeamChange}
                            required
                        />

                        <input
                            type="number"
                            name="user_id"
                            min="1"
                            placeholder="Team Member User ID"
                            value={teamForm.user_id}
                            onChange={handleTeamChange}
                            required
                        />

                        <select
                            name="role"
                            value={teamForm.role}
                            onChange={handleTeamChange}
                        >
                            <option value="support_investigator">Support Investigator</option>
                            <option value="analyst_support">Analyst Support</option>
                            <option value="supervisor_observer">Supervisor Observer</option>
                        </select>

                        <textarea
                            name="reason"
                            placeholder="Why this user is being added to the case team"
                            value={teamForm.reason}
                            onChange={handleTeamChange}
                        />

                        <button type="submit">Assign to Case Team</button>
                    </form>
                </section>
            </div>
            )}

            {activeWorkspace === "court-docs" && (
                <section className="supervisor-review-section">
                    <div className="supervisor-panel-header">
                        <span>Legal Compliance</span>
                        <strong>Court Documents</strong>
                    </div>
                    <div className="supervisor-grid">
                        <section className="supervisor-panel">
                            <h2>Warrants, Subpoenas, and Court Orders</h2>
                            <p>
                                Use this workspace to track legal authority tied to partner
                                records, search warrants, subpoenas, wiretap orders, and court
                                approved requests.
                            </p>
                            <Link to="/legal-orders">Open Legal Orders</Link>
                        </section>
                        <section className="supervisor-panel">
                            <h2>Legal Access Requests</h2>
                            <p>
                                Review whether requests are approved, pending, denied, or missing
                                information before they are used with partner sources.
                            </p>
                            <Link to="/legal-access">Open Legal Access</Link>
                        </section>
                    </div>
                </section>
            )}

            {activeWorkspace === "bolos" && (
                <section className="supervisor-review-section">
                    <div className="supervisor-panel-header">
                        <span>Field Awareness</span>
                        <strong>BOLO Alerts</strong>
                    </div>
                    <div className="supervisor-grid">
                        <section className="supervisor-panel">
                            <h2>Create or Review BOLOs</h2>

                            {queue?.active_bolos?.length === 0 ? (
                                <p>No active BOLO alerts.</p>
                            ) : (
                                queue?.active_bolos?.map((item) => (
                                    <article key={item.bolo_id} className="queue-item bolo-preview-item">
                                        <div>
                                            <strong>{item.title}</strong>
                                            <span>{item.risk_level}</span>
                                        </div>
                                        <p>{item.description}</p>
                                    </article>
                                ))
                            )}

                            <Link to="/bolos">Open BOLO Board</Link>
                        </section>
                    </div>
                </section>
            )}

            {message && <p className="alert-banner">{message}</p>}

            {queue && activeWorkspace === "access" && (

                // Each panel represents a supervisor review category. Keeping them separate
                // makes the page scannable during active investigations

                <section className="supervisor-review-section">
                    <div className="supervisor-panel-header">
                        <span>Review Queue</span>
                        <strong>Items Requiring Oversight</strong>
                    </div>
                    <div className="supervisor-grid">
                    <section className="supervisor-panel">
                        <h2>Pending Legal Access</h2>

                        {queue.pending_legal_requests.length === 0 ? (
                            <p>No pending legal requests.</p>
                        ) : (
                            queue.pending_legal_requests.map((item) => (
                                <article key={item.request_id} className="queue-item">
                                    <div>
                                        <strong>{item.source_type}</strong>
                                        <span>{item.status}</span>
                                    </div>
                                    <p>{item.purpose}</p>
                                    <Link to="/legal-access">Review Legal Queue</Link>
                                </article>
                            ))
                        )}
                    </section>

                    <section className="supervisor-panel">
                        <h2>Pending Case Access</h2>

                        {(queue.pending_case_access || []).length === 0 ? (
                            <p>No pending case access requests.</p>
                        ) : (
                            queue.pending_case_access.map((item) => (
                                <article key={item.grant_id} className="queue-item">
                                    <div>
                                        <strong>Case {item.case_id}</strong>
                                        <span>User {item.user_id}</span>
                                    </div>
                                    <p>{item.reason_category || "Manual review"}</p>
                                    <p>{item.reason}</p>

                                    <textarea
                                        className="supervisor-review-notes"
                                        placeholder="Supervisor review notes"
                                        value={reviewNotes[item.grant_id] || ""}
                                        onChange={(e) =>
                                            setReviewNotes((currentNotes) => ({
                                                ...currentNotes,
                                                [item.grant_id]: e.target.value,
                                            }))
                                        }
                                    />

                                    <div className="supervisor-actions">
                                        <button
                                            type="button"
                                            onClick={() => reviewCaseAccess(item.grant_id, "approve")}
                                        >
                                            Approve
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => reviewCaseAccess(item.grant_id, "deny")}
                                        >
                                            Deny
                                        </button>
                                    </div>
                                </article>
                            ))
                        )}
                    </section>

                    <section className="supervisor-panel">
                        <h2>Recent Restricted Access</h2>

                        {queue.recent_case_access.length === 0 ? (
                            <p>No recent restricted access.</p>
                        ) : (
                            queue.recent_case_access.map((item) => (
                                <article key={item.grant_id} className="queue-item">
                                    <div>
                                        <strong>Case {item.case_id}</strong>
                                        <span>User {item.user_id}</span>
                                    </div>
                                    <p>{item.reason}</p>
                                </article>
                            ))
                        )}
                    </section>
                    </div>
                </section>
            )}
        </div>
    );
}

export default SupervisorQueue;
