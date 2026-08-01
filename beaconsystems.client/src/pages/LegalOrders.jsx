import React, { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { apiGet, apiPost } from "../api.jsx";
import ActiveFilterBanner from "../components/ActiveFilterBanner.jsx";

const requestTypes = [
    ["interagency_request", "Interagency Requests"],
    ["da_prosecutor_request", "DA / Prosecutor Requests"],
    ["court_order", "Court Orders"],
    ["search_warrant", "Search Warrant"],
    ["arrest_warrant", "Arrest Warrant"],
    ["subpoena", "Subpoenas"],
    ["records_request", "Records Requests"],
    ["preservation_request", "Preservation Requests"],
    ["emergency_disclosure_request", "Emergency Disclosure Request"],
    ["prosecutor_filing_packet", "Prosecutor Filing Packet"],
    ["grand_jury_request", "Grand Jury Request"],
    ["lab_submission", "Lab Submission"],
    ["evidence_transfer", "Evidence Transfer"],
];

const statusOptions = [
    ["draft", "Draft"],
    ["submitted_for_supervisor_review", "Submitted for Supervisor Review"],
    ["returned_for_edits", "Returned for Edits"],
    ["approved_by_supervisor", "Approved by Supervisor"],
    ["sent_to_da", "Sent to DA"],
    ["sent_to_court", "Sent to Court"],
    ["sent", "Sent"],
    ["awaiting_response", "Awaiting Response"],
    ["signed_approved", "Signed / Approved"],
    ["denied", "Denied"],
    ["served", "Served"],
    ["completed", "Completed"],
    ["closed", "Closed"],
];

const sourceTypes = [
    ["communications", "Communications"],
    ["cell_provider", "Cell Provider"],
    ["hospital", "Hospital"],
    ["transportation", "Transportation"],
    ["camera", "Camera"],
    ["toll", "Toll"],
    ["social_media", "Social Media"],
    ["coroner", "Medical Examiner / Coroner"],
    ["genealogy", "Genealogy"],
    ["missing_persons_organization", "Missing Persons Organization"],
    ["other", "Other"],
];

const priorities = [
    ["routine", "Routine"],
    ["medium", "Medium"],
    ["high", "High"],
    ["urgent", "Urgent"],
    ["critical", "Critical"],
];

const closedStatuses = new Set(["completed", "closed", "denied"]);

const labelFor = (options, value) =>
    options.find(([optionValue]) => optionValue === value)?.[1] ||
    String(value || "Not recorded").replaceAll("_", " ");

const formatDate = (value) => {
    if (!value) {
        return "Not set";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "Not set";
    }

    return date.toLocaleDateString();
};

const fetchLegalOrders = async () => {
    const data = await apiGet("/legal-access/");
    const legalTypes = new Set(requestTypes.map(([value]) => value));
    const legacyTypes = new Set([
        "court_order",
        "warrant",
        "search_warrant",
        "subpoena",
        "wiretap_order",
        "national_security_letter",
    ]);

    return Array.isArray(data)
        ? data.filter((item) =>
            legalTypes.has(item.request_type || item.authority_type) ||
            legacyTypes.has(item.authority_type)
        )
        : [];
};

function LegalOrders() {
    const [searchParams, setSearchParams] = useSearchParams();
    const statusFilter = searchParams.get("status") || "";
    const username = localStorage.getItem("username") || "";
    const role = localStorage.getItem("role") || "viewer";
    const isSupervisor = role === "supervisor";
    const [orders, setOrders] = useState([]);
    const [message, setMessage] = useState("");
    const [selectedType, setSelectedType] = useState("all");
    const [showMoreActive, setShowMoreActive] = useState(false);
    const [showMoreClosed, setShowMoreClosed] = useState(false);
    const [form, setForm] = useState({
        request_type: "da_prosecutor_request",
        case_number: "",
        person_id: "",
        requester_name: username,
        assigned_investigator_id: "",
        receiving_entity: "",
        reason_for_request: "",
        probable_cause_summary: "",
        status: "draft",
        priority: "routine",
        due_date: "",
        approved_by_user_id: "",
        attachments: "",
        source_type: "communications",
        target_identifier: "",
        jurisdiction: "",
        legal_reference: "",
        minimization_plan: "",
        retention_plan: "",
    });

    const loadOrders = async () => {
        const data = await fetchLegalOrders();
        setOrders(data);
    };

    useEffect(() => {
        let isMounted = true;

        fetchLegalOrders()
            .then((data) => {
                if (isMounted) {
                    setOrders(data);
                }
            })
            .catch((err) => {
                console.error(err);

                if (isMounted) {
                    setMessage(err.message || "Could not load legal orders.");
                }
            });

        return () => {
            isMounted = false;
        };
    }, []);

    const filteredOrders = useMemo(() => {
        const typeFiltered = selectedType === "all"
            ? orders
            : orders.filter((order) =>
                (order.request_type || order.authority_type) === selectedType
            );

        if (!statusFilter) {
            return typeFiltered;
        }

        if (statusFilter === "pending") {
            return typeFiltered.filter((order) => !closedStatuses.has(order.status));
        }

        return typeFiltered.filter((order) => order.status === statusFilter);
    }, [orders, selectedType, statusFilter]);

    const activeOrders = filteredOrders.filter((order) =>
        !closedStatuses.has(order.status)
    );
    const closedOrders = filteredOrders.filter((order) =>
        closedStatuses.has(order.status)
    );

    const requestTypeCounts = requestTypes.map(([value, label]) => [
        value,
        label,
        orders.filter((order) => (order.request_type || order.authority_type) === value).length,
    ]);

    const handleChange = (event) => {
        setForm((current) => ({
            ...current,
            [event.target.name]: event.target.value,
        }));
    };

    const submitOrder = async (event) => {
        event.preventDefault();
        setMessage("");

        const payload = {
            case_number: form.case_number.trim(),
            person_id: form.person_id ? Number(form.person_id) : null,
            assigned_investigator_id: form.assigned_investigator_id
                ? Number(form.assigned_investigator_id)
                : null,
            approved_by_user_id: form.approved_by_user_id
                ? Number(form.approved_by_user_id)
                : null,
            requester_name: form.requester_name,
            requester_organization: form.receiving_entity,
            requester_role: "supervisor",
            contact_email: null,
            authority_type: form.request_type,
            request_type: form.request_type,
            source_type: form.source_type,
            receiving_entity: form.receiving_entity,
            target_identifier: form.target_identifier,
            jurisdiction: form.jurisdiction,
            legal_reference: form.legal_reference,
            purpose: form.reason_for_request,
            reason_for_request: form.reason_for_request,
            scope_description: form.probable_cause_summary,
            probable_cause_summary: form.probable_cause_summary,
            minimization_plan: form.minimization_plan,
            retention_plan: form.retention_plan,
            document_location: form.attachments,
            attachments: form.attachments,
            priority: form.priority,
            status: form.status,
            due_date: form.due_date ? new Date(form.due_date).toISOString() : null,
        };

        try {
            await apiPost("/legal-access/", payload);

            setMessage("Legal request record created and audit logged.");
            setForm((current) => ({
                ...current,
                case_number: "",
                person_id: "",
                assigned_investigator_id: "",
                receiving_entity: "",
                reason_for_request: "",
                probable_cause_summary: "",
                due_date: "",
                approved_by_user_id: "",
                attachments: "",
                target_identifier: "",
                jurisdiction: "",
                legal_reference: "",
                minimization_plan: "",
                retention_plan: "",
            }));
            await loadOrders();
        } catch (err) {
            console.error(err);
            setMessage(err.message || "Could not create legal request.");
        }
    };

    const assignedToLabel = (order) => {
        if (order.assigned_to) {
            return order.assigned_to;
        }

        if (order.assigned_investigator_name) {
            return order.assigned_investigator_name;
        }

        if (order.assigned_investigator_id) {
            return `User ${order.assigned_investigator_id}`;
        }

        return "Unassigned";
    };

    const supervisorRows = filteredOrders.length > 0
        ? filteredOrders
        : [
            {
                request_id: "sample-search-warrant",
                request_type: "warrant",
                display_type: "Search Warrant",
                case_number: "MP-2026-000001",
                status: "sent_to_da",
                assigned_to: "Det. Smith",
            },
            {
                request_id: "sample-phone-records",
                request_type: "records_request",
                display_type: "Phone Records",
                case_number: "MP-2026-000002",
                status: "awaiting_response",
                assigned_to: "Analyst Garcia",
            },
            {
                request_id: "sample-rfi",
                request_type: "interagency_request",
                display_type: "Interagency RFI",
                case_number: "MP-2026-000003",
                status: "completed",
                assigned_to: "Det. Jones",
            },
            {
                request_id: "sample-preservation",
                request_type: "preservation_request",
                display_type: "Preservation Req.",
                case_number: "MP-2026-000004",
                status: "sent",
                assigned_to: "Det. Smith",
            },
        ];

    const renderOrderCard = (order) => (
        <article key={order.request_id} className="legal-request-card">
            <div className="legal-request-topline">
                <Link to={`/legal-orders/${order.request_id}`}>
                    {labelFor(requestTypes, order.request_type || order.authority_type)}
                </Link>
                <span className={`request-status ${order.status}`}>
                    {labelFor(statusOptions, order.status)}
                </span>
            </div>
            <dl className="legal-record-details">
                <div>
                    <dt>Case Number</dt>
                    <dd>{order.case_number || "Unlinked"}</dd>
                </div>
                <div>
                    <dt>Person ID</dt>
                    <dd>{order.person_id ?? "Unlinked"}</dd>
                </div>
                <div>
                    <dt>Requested By</dt>
                    <dd>{order.requester_name}</dd>
                </div>
                <div>
                    <dt>Assigned Investigator</dt>
                    <dd>{order.assigned_investigator_id ?? "Not assigned"}</dd>
                </div>
                <div>
                    <dt>Receiving Agency / Court / DA</dt>
                    <dd>{order.receiving_entity || order.requester_organization}</dd>
                </div>
                <div>
                    <dt>Priority</dt>
                    <dd>{labelFor(priorities, order.priority)}</dd>
                </div>
                <div>
                    <dt>Submitted Date</dt>
                    <dd>{formatDate(order.requested_at)}</dd>
                </div>
                <div>
                    <dt>Due Date</dt>
                    <dd>{formatDate(order.due_date)}</dd>
                </div>
                <div>
                    <dt>Approved By</dt>
                    <dd>{order.approved_by_user_id || order.reviewed_by_user_id || "Pending"}</dd>
                </div>
                <div>
                    <dt>Attachments</dt>
                    <dd>{order.attachments || order.document_location || "None linked"}</dd>
                </div>
            </dl>
            <p><strong>Reason:</strong> {order.reason_for_request || order.purpose}</p>
            <p><strong>Probable Cause / Summary:</strong> {order.probable_cause_summary || order.scope_description}</p>
            <p><strong>Audit Log:</strong> Created as request #{order.request_id}; lifecycle actions are recorded in Beacon audit activity.</p>
        </article>
    );

    return (
        <div className="legal-access-page legal-orders-page">
            <div className="legal-access-header">
                <h1>Legal Orders</h1>
            </div>

            {message && <p className="alert-banner">{message}</p>}

            <section className="legal-request-type-grid" aria-label="Legal request categories">
                <button
                    type="button"
                    className={selectedType === "all" ? "active" : ""}
                    onClick={() => setSelectedType("all")}
                >
                    <span>Requests</span>
                    <strong>{orders.length}</strong>
                </button>
                {requestTypeCounts.map(([value, label, count]) => (
                    <button
                        key={value}
                        type="button"
                        className={selectedType === value ? "active" : ""}
                        onClick={() => setSelectedType(value)}
                    >
                        <span>{label}</span>
                        <strong>{count}</strong>
                    </button>
                ))}
            </section>

            {statusFilter && (
                <ActiveFilterBanner onClear={() => setSearchParams({})}>
                    {statusFilter === "pending"
                        ? "Showing active legal order requests"
                        : `Showing ${labelFor(statusOptions, statusFilter)} requests`}
                </ActiveFilterBanner>
            )}

            {isSupervisor ? (
                <section className="legal-panel legal-supervisor-tracker">
                    <div className="legal-request-table">
                        <div className="legal-request-table-head">
                            <span>Request Type</span>
                            <span>Case Number</span>
                            <span>Status</span>
                            <span>Assigned To</span>
                        </div>
                        {supervisorRows.map((order) => {
                            const isSample = String(order.request_id).startsWith("sample-");
                            const rowContent = (
                                <>
                                    <span>
                                        {order.display_type || labelFor(requestTypes, order.request_type || order.authority_type)}
                                    </span>
                                    <span>{order.case_number || "Unlinked"}</span>
                                    <span>{labelFor(statusOptions, order.status)}</span>
                                    <span>{assignedToLabel(order)}</span>
                                </>
                            );

                            return isSample ? (
                                <div
                                    key={order.request_id}
                                    className="legal-request-table-row"
                                >
                                    {rowContent}
                                </div>
                            ) : (
                                <Link
                                    key={order.request_id}
                                    to={`/legal-orders/${order.request_id}`}
                                    className="legal-request-table-row"
                                >
                                    {rowContent}
                                </Link>
                            );
                        })}
                    </div>
                </section>
            ) : (
            <div className="legal-access-layout legal-orders-layout">
                <section className="legal-panel legal-order-form-panel">
                    <h2>New Request Record</h2>

                    <form className="legal-form legal-order-form" onSubmit={submitOrder}>
                        <select name="request_type" value={form.request_type} onChange={handleChange}>
                            {requestTypes.map(([value, label]) => (
                                <option key={value} value={value}>{label}</option>
                            ))}
                        </select>
                        <input
                            name="case_number"
                            placeholder="Case Number (for example, MP-2026-000001)"
                            value={form.case_number}
                            onChange={handleChange}
                            required
                        />
                        <input name="person_id" placeholder="Person ID" value={form.person_id} onChange={handleChange} />
                        <input name="requester_name" placeholder="Requested by" value={form.requester_name} onChange={handleChange} required />
                        <input name="assigned_investigator_id" placeholder="Assigned Investigator User ID" value={form.assigned_investigator_id} onChange={handleChange} />
                        <input name="receiving_entity" placeholder="Receiving agency, court, or DA" value={form.receiving_entity} onChange={handleChange} required />
                        <select name="source_type" value={form.source_type} onChange={handleChange}>
                            {sourceTypes.map(([value, label]) => (
                                <option key={value} value={value}>{label}</option>
                            ))}
                        </select>
                        <select name="status" value={form.status} onChange={handleChange}>
                            {statusOptions.map(([value, label]) => (
                                <option key={value} value={value}>{label}</option>
                            ))}
                        </select>
                        <select name="priority" value={form.priority} onChange={handleChange}>
                            {priorities.map(([value, label]) => (
                                <option key={value} value={value}>{label}</option>
                            ))}
                        </select>
                        <input type="date" name="due_date" value={form.due_date} onChange={handleChange} />
                        <input name="approved_by_user_id" placeholder="Approved By User ID" value={form.approved_by_user_id} onChange={handleChange} />
                        <input name="target_identifier" placeholder="Subject, account, device, plate, route, or location" value={form.target_identifier} onChange={handleChange} />
                        <input name="jurisdiction" placeholder="Jurisdiction" value={form.jurisdiction} onChange={handleChange} />
                        <input name="legal_reference" placeholder="Docket, warrant, subpoena, or request number" value={form.legal_reference} onChange={handleChange} />
                        <input name="attachments" placeholder="Attachments or secure document path" value={form.attachments} onChange={handleChange} />
                        <textarea name="reason_for_request" placeholder="Reason for Request" value={form.reason_for_request} onChange={handleChange} required />
                        <textarea name="probable_cause_summary" placeholder="Probable Cause / Summary" value={form.probable_cause_summary} onChange={handleChange} required />
                        <textarea name="minimization_plan" placeholder="Minimization plan" value={form.minimization_plan} onChange={handleChange} />
                        <textarea name="retention_plan" placeholder="Retention and deletion plan" value={form.retention_plan} onChange={handleChange} />

                        <button type="submit">Create Request Record</button>
                    </form>
                </section>

                <section className="legal-panel legal-order-queue-panel">
                    <h2>Active Request Records</h2>
                    {activeOrders.length === 0 ? (
                        <p>No active legal request records.</p>
                    ) : (
                        <div className="legal-request-list">
                            {activeOrders.slice(0, showMoreActive ? 6 : 2).map(renderOrderCard)}
                            {activeOrders.length > 2 && (
                                <button
                                    type="button"
                                    className="list-toggle-button"
                                    onClick={() => setShowMoreActive((current) => !current)}
                                >
                                    {showMoreActive ? "Show fewer" : `Show ${Math.min(4, activeOrders.length - 2)} more requests`}
                                </button>
                            )}
                        </div>
                    )}
                </section>

                <section className="legal-panel legal-order-queue-panel">
                    <h2>Completed / Closed Records</h2>
                    {closedOrders.length === 0 ? (
                        <p>No completed or closed legal request records.</p>
                    ) : (
                        <div className="legal-request-list">
                            {closedOrders.slice(0, showMoreClosed ? 6 : 2).map(renderOrderCard)}
                            {closedOrders.length > 2 && (
                                <button
                                    type="button"
                                    className="list-toggle-button"
                                    onClick={() => setShowMoreClosed((current) => !current)}
                                >
                                    {showMoreClosed ? "Show fewer" : `Show ${Math.min(4, closedOrders.length - 2)} more records`}
                                </button>
                            )}
                        </div>
                    )}
                </section>
            </div>
            )}
        </div>
    );
}

export default LegalOrders;
