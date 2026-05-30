import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";


// SupervisorQueue gives agency leadership one place to review items that need
// oversight before action: legal access, partner integrations, restricted case
// access, high-priority cases, and active BOLO alerts.

function SupervisorQueue() {
    const [queue, setQueue] = useState(null);
    const [message, setMessage] = useState("");
    const [reviewNotes, setReviewNotes] = useState({});

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



    return (
        <div className="supervisor-page">
            <div className="supervisor-header">
                <h1>Supervisor Review Queue</h1>
                <p>Central review area for high-risk operational and compliance items.</p>
            </div>

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
