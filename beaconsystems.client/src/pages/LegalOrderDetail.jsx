import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

const requestTypeLabels = {
    interagency_request: "Interagency Request",
    da_prosecutor_request: "DA / Prosecutor Request",
    court_order: "Court Order",
    warrant: "Warrant",
    search_warrant: "Search Warrant",
    subpoena: "Subpoena",
    records_request: "Records Request",
    preservation_request: "Preservation Request",
};

const statusLabels = {
    draft: "Draft",
    submitted_for_supervisor_review: "Submitted for Supervisor Review",
    returned_for_edits: "Returned for Edits",
    approved_by_supervisor: "Approved by Supervisor",
    sent_to_da: "Sent to DA",
    sent_to_court: "Sent to Court",
    sent: "Sent",
    awaiting_response: "Awaiting Response",
    signed_approved: "Signed / Approved",
    denied: "Denied",
    served: "Served",
    completed: "Completed",
    closed: "Closed",
    pending: "Pending",
    approved: "Approved",
    missing_info: "Returned for Edits",
};

const priorityLabels = {
    routine: "Routine",
    medium: "Medium",
    high: "High",
    urgent: "Urgent",
    critical: "Critical",
};

const labelFor = (labels, value) =>
    labels[value] || String(value || "Not recorded").replaceAll("_", " ");

const formatDate = (value) => {
    if (!value) {
        return "Not recorded";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "Not recorded";
    }

    return date.toLocaleString();
};

function DetailField({ label, value, wide = false }) {
    return (
        <div className={wide ? "legal-detail-field wide" : "legal-detail-field"}>
            <span>{label}</span>
            <strong>{value || "Not recorded"}</strong>
        </div>
    );
}

function LegalOrderDetail() {
    const { id } = useParams();
    const [request, setRequest] = useState(null);
    const [message, setMessage] = useState("");

    useEffect(() => {
        let isMounted = true;
        const token = localStorage.getItem("token");

        const loadRequest = async () => {
            try {
                const response = await fetch(`http://127.0.0.1:8000/legal-access/${id}`, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.detail || "Could not load legal request");
                }

                const data = await response.json();

                if (isMounted) {
                    setRequest(data);
                    setMessage("");
                }
            } catch (err) {
                console.error(err);

                if (isMounted) {
                    setMessage(err.message || "Could not load legal request.");
                }
            }
        };

        loadRequest();

        return () => {
            isMounted = false;
        };
    }, [id]);

    return (
        <div className="legal-access-page legal-order-detail-page">
            <div className="legal-access-header">
                <h1>Legal Request Record</h1>
            </div>

            {message && <p className="alert-banner">{message}</p>}

            {!request ? (
                <section className="legal-panel legal-detail-panel">
                    <p>Loading legal request record...</p>
                </section>
            ) : (
                <>
                    <section className="legal-panel legal-detail-panel">
                        <div className="legal-detail-header">
                            <div>
                                <span>Request Type</span>
                                <h2>{labelFor(requestTypeLabels, request.request_type || request.authority_type)}</h2>
                            </div>
                            <Link to="/legal-orders">Back to Legal Orders</Link>
                        </div>

                        <div className="legal-detail-grid">
                            <DetailField label="Case ID" value={request.case_id} />
                            <DetailField label="Person ID" value={request.person_id} />
                            <DetailField
                                label="Requested By"
                                value={request.requested_by_name || request.requester_name}
                            />
                            <DetailField
                                label="Assigned Investigator"
                                value={request.assigned_investigator_name || request.assigned_investigator_id}
                            />
                            <DetailField
                                label="Receiving Agency / Court / DA"
                                value={request.receiving_entity || request.requester_organization}
                            />
                            <DetailField label="Status" value={labelFor(statusLabels, request.status)} />
                            <DetailField label="Priority" value={labelFor(priorityLabels, request.priority)} />
                            <DetailField label="Submitted Date" value={formatDate(request.requested_at)} />
                            <DetailField label="Due Date" value={formatDate(request.due_date)} />
                            <DetailField
                                label="Approved By"
                                value={request.approved_by_name || request.approved_by_user_id}
                            />
                            <DetailField
                                label="Attachments"
                                value={request.attachments || request.document_location}
                                wide
                            />
                            <DetailField
                                label="Reason for Request"
                                value={request.reason_for_request || request.purpose}
                                wide
                            />
                            <DetailField
                                label="Probable Cause / Summary"
                                value={request.probable_cause_summary || request.scope_description}
                                wide
                            />
                        </div>
                    </section>

                    <section className="legal-panel legal-detail-panel">
                        <div className="legal-detail-header">
                            <div>
                                <span>Audit Log</span>
                                <h2>Lifecycle Activity</h2>
                            </div>
                        </div>

                        {(request.audit_log || []).length === 0 ? (
                            <p>No audit activity recorded for this request yet.</p>
                        ) : (
                            <div className="legal-audit-list">
                                {request.audit_log.map((entry) => (
                                    <article key={entry.id} className="legal-audit-entry">
                                        <strong>{entry.action}</strong>
                                        <span>{formatDate(entry.timestamp)}</span>
                                        <p>{entry.details || "No details recorded."}</p>
                                    </article>
                                ))}
                            </div>
                        )}
                    </section>
                </>
            )}
        </div>
    );
}

export default LegalOrderDetail;
