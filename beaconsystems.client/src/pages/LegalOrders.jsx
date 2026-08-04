import React, { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { apiGet, apiPost } from "../api.jsx";
import ActiveFilterBanner from "../components/ActiveFilterBanner.jsx";

const slugify = (label) => label.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");

const requestCategories = [
    {
        id: "judicial",
        label: "Judicial",
        description: "Warrants, probable cause filings, court orders, and subpoenas",
        authorityType: "court_order",
        templates: [
            "Search Warrant Affidavit", "Search Warrant", "Arrest Warrant Affidavit / Complaint",
            "Arrest Warrant", "Bench Warrant Request", "Capias Request", "Probable Cause Affidavit",
            "Return and Inventory", "Sealing Order Request", "Search Warrant Extension Request",
            "Digital Device Search Warrant", "Cell Phone Records Search Warrant",
            "Cloud Storage Search Warrant", "Financial Records Search Warrant", "Court Order for Records",
            "Court Order for DNA", "Court Order for Fingerprints", "Court Order for Medical Records",
            "Court Order for School Records", "Court Order for Mental Health Records",
            "Court Order for Financial Records", "GPS Tracking Order", "Pen Register Order",
            "Trap and Trace Order", "Electronic Surveillance Order", "CSLI Order",
            "Subpoena Duces Tecum", "Witness Subpoena", "Business Records Subpoena",
            "Medical Records Subpoena", "Bank Records Subpoena", "Employment Records Subpoena",
            "Utility Records Subpoena", "School Records Subpoena", "Pharmacy Records Subpoena",
        ],
    },
    {
        id: "prosecutor",
        label: "Prosecutor / DA",
        description: "Filing, referral, discovery, and charging packets",
        authorityType: "da_prosecutor_request",
        templates: [
            "Case Filing Packet", "Case Referral Packet", "Felony Filing Packet", "Misdemeanor Filing Packet",
            "Supplemental Report", "Follow-up Investigation Report", "Evidence Submission Packet",
            "Discovery Packet", "Witness List", "Evidence Index", "Case Status Update",
            "Charge Recommendation", "Probable Cause Summary", "Affidavit of Probable Cause",
        ],
    },
    {
        id: "emergency",
        label: "Emergency",
        description: "Time-sensitive disclosure, preservation, and exigent requests",
        authorityType: "preservation_request",
        templates: [
            "Emergency Disclosure Request", "Emergency Preservation Request", "Exigent Circumstances Request",
            "Emergency Cell Phone Ping Request", "Emergency Subscriber Information Request",
            "Emergency Social Media Preservation Request",
        ],
    },
    {
        id: "records",
        label: "Records",
        description: "Operational, communications, video, and historical records",
        authorityType: "records_request",
        templates: [
            "Criminal History Request", "CAD Records Request", "RMS Report Request", "Jail Records Request",
            "Booking Records Request", "Body Camera Video Request", "Dash Camera Video Request",
            "Dispatch Audio Request", "Radio Traffic Request", "Jail Call Recording Request",
            "License Plate Reader Data Request", "Surveillance Video Request",
        ],
    },
    {
        id: "interagency",
        label: "Interagency",
        description: "Assistance, transfers, notifications, and regional coordination",
        authorityType: "interagency_request",
        templates: [
            "Intelligence Request", "Investigative Assistance Request", "Case Transfer Request",
            "Assistance Request", "Officer Safety Bulletin", "BOLO Request", "Regional Notification",
            "Fugitive Assistance Request", "Task Force Referral", "Mutual Aid Request",
        ],
    },
    {
        id: "forensics",
        label: "Forensics / Crime Lab",
        description: "Laboratory submissions and technical examinations",
        authorityType: "agency_agreement",
        templates: [
            "Laboratory Submission Form", "DNA Submission", "Fingerprint Submission",
            "Firearms Examination Request", "Toolmark Examination Request", "Toxicology Request",
            "Controlled Substance Analysis", "Trace Evidence Examination", "Digital Forensics Request",
            "Latent Print Examination", "Biological Evidence Submission",
        ],
    },
    {
        id: "evidence",
        label: "Evidence",
        description: "Custody, transfer, release, destruction, and property workflows",
        authorityType: "agency_agreement",
        templates: [
            "Property Receipt", "Evidence Submission", "Chain of Custody", "Evidence Transfer",
            "Evidence Release", "Evidence Destruction Request", "Evidence Return Authorization",
            "Digital Evidence Upload", "Property Inventory",
        ],
    },
    {
        id: "medical_examiner",
        label: "Medical Examiner",
        description: "Decedent identification, comparison, and report requests",
        authorityType: "interagency_request",
        templates: [
            "Autopsy Report Request", "Identification Request", "Fingerprint Comparison Request",
            "Dental Record Comparison", "DNA Comparison Request", "Toxicology Report Request",
            "X-Ray Comparison Request", "Decedent Property Request", "Unidentified Remains Inquiry",
        ],
    },
    {
        id: "missing_persons",
        label: "Missing Persons",
        description: "National entries, alerts, updates, and identification resources",
        authorityType: "interagency_request",
        templates: [
            "Missing Person Entry Request (NCIC)", "NamUs Submission", "Missing Child Notification",
            "Endangered Missing Person Notification", "Silver Alert Request", "AMBER Alert Request",
            "Missing Person Update", "Missing Person Cancellation", "Family DNA Collection Request",
            "Dental Record Request", "Missing Person Poster Approval",
        ],
    },
    {
        id: "healthcare",
        label: "Hospitals / Healthcare",
        description: "Patient inquiries, welfare checks, and authorized medical requests",
        authorityType: "records_request",
        templates: [
            "Emergency Patient Inquiry", "Welfare Check Request", "Hospital Admission Inquiry",
            "Medical Records Request", "Unidentified Patient Inquiry",
        ],
    },
    {
        id: "social_services",
        label: "Social Services",
        description: "Protection, victim support, shelter, and crisis referrals",
        authorityType: "interagency_request",
        templates: [
            "Child Protective Services Referral", "Adult Protective Services Referral",
            "Victim Services Referral", "Shelter Referral", "Crisis Intervention Request",
            "Mental Health Evaluation Request",
        ],
    },
];

const requestTemplates = requestCategories.flatMap((category) =>
    category.templates.map((label) => ({
        value: `${category.id}__${slugify(label)}`,
        label,
        categoryId: category.id,
        authorityType: category.authorityType,
    }))
);
const requestTypes = requestTemplates.map(({ value, label }) => [value, label]);
const templateByValue = new Map(requestTemplates.map((template) => [template.value, template]));
const legacyCategoryByType = {
    warrant: "judicial", search_warrant: "judicial", arrest_warrant: "judicial",
    court_order: "judicial", subpoena: "judicial", wiretap_order: "judicial",
    da_prosecutor_request: "prosecutor", prosecutor_filing_packet: "prosecutor",
    grand_jury_request: "prosecutor", preservation_request: "emergency",
    emergency_disclosure_request: "emergency", records_request: "records",
    interagency_request: "interagency", lab_submission: "forensics", evidence_transfer: "evidence",
};

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
        ...Object.keys(legacyCategoryByType),
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

const categoryForOrder = (order) =>
    templateByValue.get(order.request_type)?.categoryId ||
    legacyCategoryByType[order.request_type || order.authority_type] ||
    "records";

function LegalOrders() {
    const [searchParams, setSearchParams] = useSearchParams();
    const statusFilter = searchParams.get("status") || "";
    const requestedTemplate = searchParams.get("template") || "";
    const username = localStorage.getItem("username") || "";
    const role = localStorage.getItem("role") || "viewer";
    const isSupervisor = role === "supervisor";
    const [orders, setOrders] = useState([]);
    const [message, setMessage] = useState("");
    const [selectedCategory, setSelectedCategory] = useState("all");
    const [templateSearch, setTemplateSearch] = useState("");
    const [showMoreActive, setShowMoreActive] = useState(false);
    const [showMoreClosed, setShowMoreClosed] = useState(false);
    const [form, setForm] = useState({
        request_type: templateByValue.has(requestedTemplate) ? requestedTemplate : requestTemplates[0].value,
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
        const typeFiltered = selectedCategory === "all"
            ? orders
            : orders.filter((order) => categoryForOrder(order) === selectedCategory);

        if (!statusFilter) {
            return typeFiltered;
        }

        if (statusFilter === "pending") {
            return typeFiltered.filter((order) => !closedStatuses.has(order.status));
        }

        return typeFiltered.filter((order) => order.status === statusFilter);
    }, [orders, selectedCategory, statusFilter]);

    const activeOrders = filteredOrders.filter((order) =>
        !closedStatuses.has(order.status)
    );
    const closedOrders = filteredOrders.filter((order) =>
        closedStatuses.has(order.status)
    );

    const categoryCounts = requestCategories.map((category) => ({
        ...category,
        count: orders.filter((order) => categoryForOrder(order) === category.id).length,
    }));
    const visibleTemplates = requestTemplates.filter((template) => {
        const matchesCategory = selectedCategory === "all" || template.categoryId === selectedCategory;
        const searchValue = templateSearch.trim().toLowerCase();
        return matchesCategory && (!searchValue || template.label.toLowerCase().includes(searchValue));
    });

    const handleChange = (event) => {
        setForm((current) => ({
            ...current,
            [event.target.name]: event.target.value,
        }));
    };

    const submitOrder = async (event) => {
        event.preventDefault();
        setMessage("");

        const selectedTemplate = templateByValue.get(form.request_type);
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
            authority_type: selectedTemplate?.authorityType || "records_request",
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
                    className={selectedCategory === "all" ? "active" : ""}
                    onClick={() => setSelectedCategory("all")}
                >
                    <span className="legal-category-copy"><b>All Workflows</b><small>Every request and document category</small></span>
                    <strong>{orders.length}</strong>
                </button>
                {categoryCounts.map((category) => (
                    <button
                        key={category.id}
                        type="button"
                        className={selectedCategory === category.id ? "active" : ""}
                        onClick={() => setSelectedCategory(category.id)}
                    >
                        <span className="legal-category-copy"><b>{category.label}</b><small>{category.description}</small></span>
                        <strong>{category.count}</strong>
                    </button>
                ))}
            </section>

            <section className="legal-template-library" aria-label="Request template library">
                <div className="legal-template-library-header">
                    <div>
                        <span>Configurable document library</span>
                        <h2>{selectedCategory === "all" ? "All Request Templates" : requestCategories.find((category) => category.id === selectedCategory)?.label}</h2>
                        <p>Choose a workflow template. Agencies can later replace its fields and generated document with their approved local version.</p>
                    </div>
                    <input
                        type="search"
                        value={templateSearch}
                        onChange={(event) => setTemplateSearch(event.target.value)}
                        placeholder="Search templates"
                        aria-label="Search request templates"
                    />
                </div>
                <div className="legal-template-list">
                    {visibleTemplates.map((template) => (
                        <button
                            key={template.value}
                            type="button"
                            className={form.request_type === template.value ? "active" : ""}
                            onClick={() => {
                                setForm((current) => ({ ...current, request_type: template.value }));
                                setSelectedCategory(template.categoryId);
                            }}
                        >
                            <span>{template.label}</span>
                            <small>{requestCategories.find((category) => category.id === template.categoryId)?.label}</small>
                        </button>
                    ))}
                    {visibleTemplates.length === 0 && <p>No templates match this search.</p>}
                </div>
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
                            {requestCategories.map((category) => (
                                <optgroup key={category.id} label={category.label}>
                                    {requestTemplates.filter((template) => template.categoryId === category.id).map((template) => (
                                        <option key={template.value} value={template.value}>{template.label}</option>
                                    ))}
                                </optgroup>
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
