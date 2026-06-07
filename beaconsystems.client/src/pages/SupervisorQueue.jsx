import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";


// SupervisorQueue gives agency leadership one place to review items that need
// oversight before action: legal access, partner integrations, restricted case
// access, high-priority cases, and active BOLO alerts.

function SupervisorQueue() {
    const [queue, setQueue] = useState(null);
    const [message, setMessage] = useState("");
    const [reviewNotes, setReviewNotes] = useState({});
    const [users, setUsers] = useState([]);
    const [expandedSections, setExpandedSections] = useState({});
    const [teamForm, setTeamForm] = useState({
        case_id: "",
        user_id: "",
        role: "supervisor",
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
    const location = useLocation();
    const workspaceFromPath = location.pathname.split("/")[2] || "";
    const activeWorkspace = workspaceFromPath || null;

    const formatDateTime = (value) => {
        if (!value) {
            return "Not recorded";
        }

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return "Not recorded";
        }

        return date.toLocaleString();
    };

    const activeUsers = users.filter((user) => user.is_active);
    const activeInvestigators = activeUsers.filter((user) => user.role === "investigator");
    const oversightCount = (queue?.pending_legal_requests?.length || 0) +
        (queue?.pending_case_access?.length || 0) +
        (queue?.recent_case_access?.length || 0);
    const commandDashboard = queue?.command_dashboard || {};
    const investigatorWorkload = queue?.investigator_workload || [];
    const overloadedInvestigators = investigatorWorkload.filter((item) =>
        item.workload_status === "overloaded"
    );
    const capacityInvestigators = investigatorWorkload.filter((item) =>
        item.workload_status === "capacity"
    );
    const productiveInvestigators = [...investigatorWorkload]
        .sort((a, b) => (b.recent_results || 0) - (a.recent_results || 0))
        .slice(0, 6);
    const stallRiskSummary = queue?.stall_risk_summary || {};
    const leadSummary = queue?.lead_summary || {};
    const timelineSummary = queue?.timeline_summary || {};
    const agencyCoordination = queue?.agency_coordination || {};
    const workspaceCards = [
        ["personnel", "Personnel", "Staffing, users, teams, and workload.", capacityInvestigators.length],
        ["investigations", "Investigations", "Stalls, leads, timelines, sightings, and evidence.", commandDashboard.cases_needing_attention_today || 0],
        ["operations", "Operations", "Alerts, BOLOs, and urgent field activity.", commandDashboard.critical_alerts || queue?.active_bolos?.length || 0],
        ["compliance", "Compliance", "Legal, access, audit, and evidence reviews.", oversightCount],
        ["community", "Agency Coordination", "Partner agencies, shared intelligence, and requests.", agencyCoordination.shared_intelligence || exchanges.length],
        ["reports", "Reports", "Command snapshots and performance summaries.", commandDashboard.active_cases || 0],
    ];
    const visibleItems = (sectionKey, items, collapsedCount = 2, expandedCount = 6) =>
        (items || []).slice(0, expandedSections[sectionKey] ? expandedCount : collapsedCount);
    const renderListToggle = (sectionKey, totalCount, label = "items", expandedCount = 6) => {
        if (totalCount <= 2) {
            return null;
        }

        const isExpanded = expandedSections[sectionKey];
        const visibleMoreCount = Math.min(expandedCount, totalCount) - 2;

        return (
            <button
                type="button"
                className="supervisor-list-toggle"
                onClick={() =>
                    setExpandedSections((current) => ({
                        ...current,
                        [sectionKey]: !current[sectionKey],
                    }))
                }
            >
                {isExpanded ? "Show fewer" : `Show ${visibleMoreCount} more ${label}`}
            </button>
        );
    };


 // Load the review queue once when the page opens. The backend enforces that
// only admins, agency admins, and supervisors can access this endpoint.

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
                role: "supervisor",
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
                {workspaceCards.map(([key, title, description, count]) => (
                    <Link
                        key={key}
                        to={`/supervisor/${key}`}
                        className={`supervisor-admin-card ${activeWorkspace === key ? "active" : ""}`}
                    >
                        <span className="supervisor-workspace-count">{count}</span>
                        <strong>{title}</strong>
                        <small>{description}</small>
                    </Link>
                ))}
            </section>

            <section className="supervisor-command-strip" aria-label="Command dashboard">
                <article className="supervisor-metric-card">
                    <span>Active Cases</span>
                    <strong>{commandDashboard.active_cases || 0}</strong>
                    <small>Open investigations now</small>
                </article>
                <article className="supervisor-metric-card">
                    <span>High-Risk Missing Persons</span>
                    <strong>{commandDashboard.high_risk_missing_persons || 0}</strong>
                    <small>High or critical priority</small>
                </article>
                <article className="supervisor-metric-card">
                    <span>Critical Alerts</span>
                    <strong>{commandDashboard.critical_alerts || 0}</strong>
                    <small>Need command awareness</small>
                </article>
                <article className="supervisor-metric-card">
                    <span>Need Attention Today</span>
                    <strong>{commandDashboard.cases_needing_attention_today || 0}</strong>
                    <small>Stall, lead, or warrant risk</small>
                </article>
            </section>

            {activeWorkspace === "personnel" && (
            <div className="supervisor-operations-grid">
                <section className="supervisor-user-registration supervisor-capacity-card">
                    <div className="supervisor-panel-header">
                        <span>Personnel</span>
                        <strong>Investigator Capacity</strong>
                    </div>

                    <div className="supervisor-capacity-summary">
                        <span>Active investigators</span>
                        <strong>{activeInvestigators.length}</strong>
                        <small>Available staff for case assignment and support</small>
                    </div>

                    <div className="supervisor-investigator-list">
                        {activeInvestigators.length === 0 ? (
                            <p>No active investigators found for your agency.</p>
                        ) : (
                            visibleItems("activeInvestigators", activeInvestigators).map((user) => (
                                <article key={user.user_id} className="supervisor-investigator-item">
                                    <strong>{user.username}</strong>
                                    <small>{user.email}</small>
                                </article>
                            ))
                        )}
                        {renderListToggle("activeInvestigators", activeInvestigators.length, "investigators")}
                    </div>
                </section>

                <section className="supervisor-user-registration supervisor-workload-card">
                    <div className="supervisor-panel-header">
                        <span>Workload Management</span>
                        <strong>Capacity & Results</strong>
                    </div>

                    <div className="supervisor-workload-summary">
                        <div>
                            <span>Overloaded</span>
                            <strong>{overloadedInvestigators.length}</strong>
                        </div>
                        <div>
                            <span>Capacity</span>
                            <strong>{capacityInvestigators.length}</strong>
                        </div>
                        <div>
                            <span>Unassigned Cases</span>
                            <strong>{commandDashboard.unassigned_cases || 0}</strong>
                        </div>
                    </div>

                    <div className="supervisor-investigator-list">
                        {investigatorWorkload.length === 0 ? (
                            <p>No workload data available yet.</p>
                        ) : (
                            visibleItems("investigatorWorkload", investigatorWorkload).map((item) => (
                                <article key={item.user_id} className={`supervisor-workload-item ${item.workload_status}`}>
                                    <div>
                                        <strong>{item.username}</strong>
                                        <span>{item.workload_status}</span>
                                    </div>
                                    <p>{item.active_cases} active cases | {item.recent_results} recent actions</p>
                                </article>
                            ))
                        )}
                        {renderListToggle("investigatorWorkload", investigatorWorkload.length, "investigators")}
                    </div>
                </section>

                <section className="case-team-panel">
                    <div className="supervisor-panel-header">
                        <span>Case Team</span>
                        <strong>Assemble Case Team</strong>
                    </div>

                    <p className="supervisor-panel-note">
                        Assign the supervisor, lead investigator, analysts, evidence
                        technicians, coordinators, agency partners, or command staff.
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

                        <select
                            name="user_id"
                            value={teamForm.user_id}
                            onChange={handleTeamChange}
                            required
                        >
                            <option value="">Select team member</option>
                            {activeUsers.map((user) => (
                                <option
                                    key={user.user_id}
                                    value={user.user_id}
                                >
                                    {user.username} ({user.role})
                                </option>
                            ))}
                        </select>

                        <select
                            name="role"
                            value={teamForm.role}
                        onChange={handleTeamChange}
                    >
                        <option value="supervisor">Supervisor</option>
                        <option value="lead_investigator">Lead Investigator</option>
                        <option value="investigator">Investigator</option>
                        <option value="intelligence_analyst">Intelligence Analyst</option>
                        <option value="evidence_technician">Evidence Technician</option>
                        <option value="tip_coordinator">Tip Coordinator</option>
                        <option value="external_agency_user">External Agency User</option>
                        <option value="administrator">Administrator</option>
                        <option value="command_staff">Command Staff</option>
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

            {activeWorkspace === "investigations" && (
            <div className="supervisor-operations-grid">
                <section className="case-team-panel supervisor-stall-panel">
                    <div className="supervisor-panel-header">
                        <span>Stall Risk</span>
                        <strong>Needs Attention Today</strong>
                    </div>

                    <div className="supervisor-risk-grid">
                        <span>No activity 7+ days<strong>{stallRiskSummary.inactive_7_days || 0}</strong></span>
                        <span>No activity 14+ days<strong>{stallRiskSummary.inactive_14_days || 0}</strong></span>
                        <span>No activity 30+ days<strong>{stallRiskSummary.inactive_30_days || 0}</strong></span>
                        <span>Unassigned leads<strong>{stallRiskSummary.unassigned_leads || 0}</strong></span>
                        <span>Missing follow-ups<strong>{stallRiskSummary.missing_followups || 0}</strong></span>
                        <span>Pending warrants<strong>{stallRiskSummary.pending_warrants || 0}</strong></span>
                        <span>Missing reports<strong>{stallRiskSummary.missing_reports || 0}</strong></span>
                    </div>
                </section>

                <section className="case-team-panel">
                    <div className="supervisor-panel-header">
                        <span>Lead Management</span>
                        <strong>Lead Follow-Up Queue</strong>
                    </div>

                    <div className="supervisor-report-grid">
                        <span>New Leads<strong>{leadSummary.new || 0}</strong></span>
                        <span>Assigned Leads<strong>{leadSummary.assigned || 0}</strong></span>
                        <span>Pending Leads<strong>{leadSummary.pending || 0}</strong></span>
                        <span>Closed Leads<strong>{leadSummary.closed || 0}</strong></span>
                    </div>
                    <p className="supervisor-panel-note">
                        Overdue follow-ups: {leadSummary.overdue_followups || 0}
                    </p>
                    <Link to="/intelligence">Open Leads & Sightings</Link>
                </section>

                <section className="case-team-panel">
                    <div className="supervisor-panel-header">
                        <span>Case Command</span>
                        <strong>Investigations Oversight</strong>
                    </div>

                    <p className="supervisor-panel-note">
                        Create cases, review agency-wide case progress, approve closure work,
                        and reassign investigative resources when a case needs support.
                    </p>

                    <div className="supervisor-action-grid">
                        <Link to="/create-case">Create Case</Link>
                        <Link to="/cases">Review Case Status</Link>
                        <Link to="/intelligence">Review Leads & Sightings</Link>
                        <Link to="/evidence-upload">Review Evidence Handling</Link>
                    </div>
                </section>

                <section className="case-team-panel">
                    <div className="supervisor-panel-header">
                        <span>Case Progress</span>
                        <strong>Cases Needing Command Attention</strong>
                    </div>

                    {(queue?.high_priority_cases || []).length === 0 ? (
                        <p>No command attention items surfaced.</p>
                    ) : (
                        <div className="supervisor-user-list">
                            {visibleItems("highPriorityCases", queue.high_priority_cases).map((item) => (
                                <article key={item.case_id} className="queue-item">
                                    <div>
                                        <strong>{item.case_number}</strong>
                                        <span>{item.case_status}</span>
                                    </div>
                                    <p>{item.title}</p>
                                    <p className="queue-item-meta">
                                        Assigned to: {item.investigator_name || (
                                            item.investigator_id
                                                ? `Investigator ${item.investigator_id}`
                                                : "Unassigned"
                                        )}
                                    </p>
                                    <Link to={`/cases/${item.case_id}`}>Open Case</Link>
                                </article>
                            ))}
                            {renderListToggle("highPriorityCases", queue.high_priority_cases.length, "cases")}
                        </div>
                    )}
                </section>

                <section className="case-team-panel supervisor-timeline-panel">
                    <div className="supervisor-panel-header">
                        <span>Timeline Management</span>
                        <strong>Recent Case Activity</strong>
                    </div>

                    <div className="supervisor-timeline-list">
                        {(timelineSummary.recent_events || []).length === 0 ? (
                            <p>No recent timeline events found.</p>
                        ) : (
                            visibleItems("timelineEvents", timelineSummary.recent_events).map((event) => (
                                <article key={event.event_id} className="supervisor-timeline-item">
                                    <strong>{event.case_number} | {event.event_type}</strong>
                                    <span>{formatDateTime(event.timestamp)}</span>
                                    <p>{event.description || event.location || "No details recorded."}</p>
                                </article>
                            ))
                        )}
                        {renderListToggle("timelineEvents", (timelineSummary.recent_events || []).length, "events")}
                    </div>
                </section>

                <section className="case-team-panel">
                    <div className="supervisor-panel-header">
                        <span>Signals</span>
                        <strong>Sightings & Evidence</strong>
                    </div>

                    <div className="supervisor-signal-grid">
                        <div>
                            <h3>Recent Sightings</h3>
                            {(timelineSummary.recent_sightings || []).length === 0 ? (
                                <p>No recent sightings.</p>
                            ) : (
                                visibleItems("recentSightings", timelineSummary.recent_sightings).map((sighting) => (
                                    <article key={sighting.sighting_id} className="supervisor-mini-item">
                                        <strong>{sighting.case_number}</strong>
                                        <span>{sighting.location || "Location not recorded"}</span>
                                    </article>
                                ))
                            )}
                            {renderListToggle("recentSightings", (timelineSummary.recent_sightings || []).length, "sightings")}
                        </div>
                        <div>
                            <h3>Evidence Collected</h3>
                            {(timelineSummary.recent_evidence || []).length === 0 ? (
                                <p>No recent evidence.</p>
                            ) : (
                                visibleItems("recentEvidence", timelineSummary.recent_evidence).map((item) => (
                                    <article key={item.evidence_id} className="supervisor-mini-item">
                                        <strong>{item.case_number}</strong>
                                        <span>{item.evidence_type} | {item.custody_status || "collected"}</span>
                                    </article>
                                ))
                            )}
                            {renderListToggle("recentEvidence", (timelineSummary.recent_evidence || []).length, "items")}
                        </div>
                    </div>
                </section>
            </div>
            )}

            {activeWorkspace === "community" && (
            <div className="supervisor-operations-grid">
                <section className="case-team-panel supervisor-coordination-panel">
                    <div className="supervisor-panel-header">
                        <span>Regional Coordination</span>
                        <strong>Agency Involvement</strong>
                    </div>

                    <div className="supervisor-report-grid">
                        <span>Agencies Involved<strong>{(agencyCoordination.involved_agencies || []).length}</strong></span>
                        <span>Shared Intelligence<strong>{agencyCoordination.shared_intelligence || 0}</strong></span>
                        <span>Joint Investigations<strong>{agencyCoordination.joint_investigations || 0}</strong></span>
                        <span>Outstanding Requests<strong>{agencyCoordination.outstanding_requests || 0}</strong></span>
                    </div>

                    <div className="supervisor-agency-list">
                        {(agencyCoordination.involved_agencies || []).length === 0 ? (
                            <p>No partner agency activity surfaced yet.</p>
                        ) : (
                            visibleItems("involvedAgencies", agencyCoordination.involved_agencies).map((agency) => (
                                <span key={agency}>{agency}</span>
                            ))
                        )}
                        {renderListToggle("involvedAgencies", (agencyCoordination.involved_agencies || []).length, "agencies")}
                    </div>
                </section>

                <section className="agency-exchange-panel supervisor-exchange-panel">
                    <div className="agency-exchange-header">
                        <span>Agency Coordination</span>
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
                            visibleItems("agencyExchanges", exchanges).map((exchange) => (
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
                        {renderListToggle("agencyExchanges", exchanges.length, "exchanges")}
                    </div>
                </section>

            </div>
            )}

            {activeWorkspace === "compliance" && (
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

            {activeWorkspace === "operations" && (
                <section className="supervisor-review-section">
                    <div className="supervisor-panel-header">
                        <span>Operational Management</span>
                        <strong>Field Alerts & BOLOs</strong>
                    </div>
                    <div className="supervisor-grid">
                        <section className="supervisor-panel">
                            <h2>Create or Review BOLOs</h2>

                            {queue?.active_bolos?.length === 0 ? (
                                <p>No active BOLO alerts.</p>
                            ) : (
                                visibleItems("activeBolos", queue?.active_bolos || []).map((item) => (
                                    <article key={item.bolo_id} className="queue-item bolo-preview-item">
                                        <div>
                                            <strong>{item.title}</strong>
                                            <span>{item.risk_level}</span>
                                        </div>
                                        <p>{item.description}</p>
                                    </article>
                                ))
                            )}
                            {renderListToggle("activeBolos", (queue?.active_bolos || []).length, "BOLOs")}

                            <Link to="/alerts">Open Operational Alerts</Link>
                        </section>

                    </div>
                </section>
            )}

            {activeWorkspace === "reports" && (
                <section className="supervisor-review-section">
                    <div className="supervisor-panel-header">
                        <span>Command Reporting</span>
                        <strong>Supervisor Snapshot</strong>
                    </div>
                    <div className="supervisor-grid">
                        <section className="supervisor-panel">
                            <h2>Investigator Productivity</h2>
                            <div className="supervisor-report-grid">
                                <span>Overloaded investigators<strong>{overloadedInvestigators.length}</strong></span>
                                <span>With capacity<strong>{capacityInvestigators.length}</strong></span>
                                <span>Producing results<strong>{productiveInvestigators.filter((item) => item.recent_results > 0).length}</strong></span>
                                <span>Unassigned cases<strong>{commandDashboard.unassigned_cases || 0}</strong></span>
                            </div>
                            <div className="supervisor-investigator-list">
                                {visibleItems("productiveInvestigators", productiveInvestigators).map((item) => (
                                    <article key={item.user_id} className="supervisor-mini-item">
                                        <strong>{item.username}</strong>
                                        <span>{item.recent_results} recent actions | {item.active_cases} cases</span>
                                    </article>
                                ))}
                                {renderListToggle("productiveInvestigators", productiveInvestigators.length, "investigators")}
                            </div>
                        </section>

                        <section className="supervisor-panel">
                            <h2>Command Snapshot</h2>
                            <div className="supervisor-report-grid">
                                <span>Active cases<strong>{commandDashboard.active_cases || 0}</strong></span>
                                <span>High-risk persons<strong>{commandDashboard.high_risk_missing_persons || 0}</strong></span>
                                <span>Critical alerts<strong>{commandDashboard.critical_alerts || 0}</strong></span>
                                <span>Attention today<strong>{commandDashboard.cases_needing_attention_today || 0}</strong></span>
                            </div>
                        </section>

                        <section className="supervisor-panel">
                            <h2>Compliance & Audit Readiness</h2>
                            <div className="supervisor-report-grid">
                                <span>Legal reviews<strong>{queue?.pending_legal_requests?.length || 0}</strong></span>
                                <span>Access approvals<strong>{queue?.pending_case_access?.length || 0}</strong></span>
                                <span>Access log entries<strong>{queue?.recent_case_access?.length || 0}</strong></span>
                                <span>Agency exchanges<strong>{agencyCoordination.shared_intelligence || exchanges.length}</strong></span>
                            </div>
                        </section>

                    </div>
                </section>
            )}

            {message && <p className="alert-banner">{message}</p>}

            {queue && activeWorkspace === "compliance" && (

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
                            visibleItems("pendingLegalRequests", queue.pending_legal_requests).map((item) => (
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
                        {renderListToggle("pendingLegalRequests", queue.pending_legal_requests.length, "requests")}
                    </section>

                    <section className="supervisor-panel">
                        <h2>Pending Case Access</h2>

                        {(queue.pending_case_access || []).length === 0 ? (
                            <p>No pending case access requests.</p>
                        ) : (
                            visibleItems("pendingCaseAccess", queue.pending_case_access).map((item) => (
                                <article key={item.grant_id} className="queue-item">
                                    <div>
                                        <strong>{item.case_number || `Case ${item.case_id}`}</strong>
                                        <span>{item.username || `User ${item.user_id}`}</span>
                                    </div>
                                    <p>{item.case_title}</p>
                                    <p>{item.reason_category || "Manual review"} | Requested {formatDateTime(item.granted_at)}</p>
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
                        {renderListToggle("pendingCaseAccess", (queue.pending_case_access || []).length, "requests")}
                    </section>

                    <section className="supervisor-panel">
                        <h2>Recent Restricted Access</h2>

                        {queue.recent_case_access.length === 0 ? (
                            <p>No recent restricted access.</p>
                        ) : (
                            visibleItems("recentCaseAccess", queue.recent_case_access).map((item) => (
                                <article key={item.grant_id} className="queue-item">
                                    <div>
                                        <strong>{item.username || `User ${item.user_id}`}</strong>
                                        <span>{item.status}</span>
                                    </div>
                                    <p className="queue-item-meta">
                                        {item.case_number || `Case ${item.case_id}`} | {formatDateTime(item.granted_at)}
                                    </p>
                                    {item.case_title && <p>{item.case_title}</p>}
                                    <p>{item.reason}</p>
                                    {item.expires_at && (
                                        <p className="queue-item-meta">Expires {formatDateTime(item.expires_at)}</p>
                                    )}
                                </article>
                            ))
                        )}
                        {renderListToggle("recentCaseAccess", queue.recent_case_access.length, "entries")}
                    </section>
                    </div>
                </section>
            )}
        </div>
    );
}

export default SupervisorQueue;
