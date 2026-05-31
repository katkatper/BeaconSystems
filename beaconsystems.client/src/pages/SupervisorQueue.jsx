import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";


// SupervisorQueue gives agency leadership one place to review items that need
// oversight before action: legal access, partner integrations, restricted case
// access, high-priority cases, and active BOLO alerts.

function SupervisorQueue() {
    const [queue, setQueue] = useState(null);
    const [message, setMessage] = useState("");
    const [reviewNotes, setReviewNotes] = useState({});
    const [newUser, setNewUser] = useState({
        username: "",
        email: "",
        password: "",
        role: "investigator",
        agency_id: "",
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
                throw new Error(errorData.detail || "Could not register user");
            }

            const data = await response.json();
            setMessage(`${data.username} was registered as ${data.role}.`);
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

    const handleExchangeChange = (event) => {
        setExchangeForm({
            ...exchangeForm,
            [event.target.name]: event.target.value,
        });
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
                <h1>Supervisor Review Queue</h1>
                <p>Central review area for high-risk operational and compliance items.</p>
            </div>

            <section className="supervisor-admin-links" aria-label="Supervisor administration links">
                <Link to="/audit" className="supervisor-admin-card">
                    <span>Compliance</span>
                    <strong>Audit Center</strong>
                    <small>Review access, evidence, and user activity.</small>
                </Link>

                <Link to="/alerts" className="supervisor-admin-card">
                    <span>Operations</span>
                    <strong>Alerts</strong>
                    <small>Create and monitor field alerts.</small>
                </Link>

                <Link to="/admin/users" className="supervisor-admin-card">
                    <span>Administration</span>
                    <strong>Users</strong>
                    <small>Manage roles and investigator access.</small>
                </Link>
            </section>

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
                        exchanges.map((exchange) => (
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

            {message && <p className="alert-banner">{message}</p>}

            {queue && (

                // Each panel represents a supervisor review category. Keeping them separate
                // makes the page scannable during active investigations

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
                        <h2>Pending Partners</h2>

                        {queue.pending_partner_sources.length === 0 ? (
                            <p>No pending partner integrations.</p>
                        ) : (
                            queue.pending_partner_sources.map((item) => (
                                <article key={item.integration_source_id || item.id} className="queue-item">
                                    <div>
                                        <strong>{item.source_name}</strong>
                                        <span>{item.status}</span>
                                    </div>
                                    <p>{item.source_type}</p>
                                    <Link to="/partner-sources">Review Partners</Link>
                                </article>
                            ))
                        )}
                    </section>

                    <section className="supervisor-panel">
                        <h2>High Priority Cases</h2>

                        {queue.high_priority_cases.length === 0 ? (
                            <p>No high priority cases.</p>
                        ) : (
                            queue.high_priority_cases.map((item) => (
                                <article key={item.case_id} className="queue-item">
                                    <div>
                                        <strong>{item.case_number}</strong>
                                        <span>{item.priority_level}</span>
                                    </div>
                                    <p>{item.title}</p>
                                    <Link to={`/cases/${item.case_id}`}>Open Case</Link>
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

                    <section className="supervisor-panel">
                        <h2>Active BOLO Alerts</h2>

                        {queue.active_bolos.length === 0 ? (
                            <p>No active BOLO alerts.</p>
                        ) : (
                            queue.active_bolos.map((item) => (
                                <article key={item.bolo_id} className="queue-item bolo-preview-item">
                                    <div>
                                        <strong>{item.title}</strong>
                                        <span>{item.risk_level}</span>
                                    </div>
                                    <p>{item.description}</p>
                                    <Link to="/bolos">Open BOLO Board</Link>
                                </article>
                            ))
                        )}
                    </section>
                </div>
            )}
        </div>
    );
}

export default SupervisorQueue;
