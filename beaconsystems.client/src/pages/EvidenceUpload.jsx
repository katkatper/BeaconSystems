import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { apiBlob, apiGet, apiPost, apiPostForm, apiRequest } from "../api.jsx";
import ShowMoreControls from "../components/ShowMoreControls.jsx";

const fetchEvidence = async (caseFilter = "") => {
    return apiGet(caseFilter ? `/evidence/?case_id=${caseFilter}` : "/evidence/");
};

const normalizeStatus = (status) => status || "collected";
const getEvidenceIndicator = (status) => {
    const normalized = normalizeStatus(status);

    if (["stored", "archived", "results_returned"].includes(normalized)) {
        return ["In Storage", "storage"];
    }

    if (["submitted", "at_lab", "in_analysis"].includes(normalized)) {
        return ["At Lab", "lab"];
    }

    if (["missing", "overdue_review"].includes(normalized)) {
        return ["Action Required", "action"];
    }

    return ["Collected", "collected"];
};

const evidenceDate = (item) =>
    item.uploaded_at || item.created_at || item.collected_at || item.available_at || null;

const isThisWeek = (dateValue) => {
    if (!dateValue) {
        return false;
    }

    const itemDate = new Date(dateValue);
    if (Number.isNaN(itemDate.getTime())) {
        return false;
    }

    const today = new Date();
    const weekAgo = new Date(today);
    weekAgo.setDate(today.getDate() - 7);

    return itemDate >= weekAgo && itemDate <= today;
};

function EvidenceUpload() {
    const [searchParams, setSearchParams] = useSearchParams();
    const statusFilter = searchParams.get("status") || "all";
    const [caseId, setCaseId] = useState("");
    const [filterCaseId, setFilterCaseId] = useState("");
    const [evidenceType, setEvidenceType] = useState("");
    const [description, setDescription] = useState("");
    const [file, setFile] = useState(null);
    const [evidence, setEvidence] = useState([]);
    const [evidenceChains, setEvidenceChains] = useState({});
    const [custodyForms, setCustodyForms] = useState({});
    const [visibleEvidenceCount, setVisibleEvidenceCount] = useState(2);
    const [message, setMessage] = useState("");
    const custodyActions = [
        ["TRANSFERRED", "Transferred"],
        ["SUBMITTED_TO_LAB", "Sent to lab"],
        ["LAB_RECEIVED", "Lab received"],
        ["LAB_ANALYSIS_STARTED", "Analysis started"],
        ["LAB_RESULTS_RETURNED", "Lab results returned"],
        ["RETURNED_TO_AGENCY", "Returned to agency"],
        ["STORED", "Stored"],
        ["RELEASED", "Released"],
        ["MISSING", "Missing"],
        ["OVERDUE_REVIEW", "Overdue review"],
        ["AUDIT_REVIEWED", "Audit reviewed"],
    ];
    const statusCounts = evidence.reduce(
        (counts, item) => {
            const status = normalizeStatus(item.custody_status);
            return {
                ...counts,
                [status]: (counts[status] || 0) + 1,
            };
        },
        {
            collected: 0,
            submitted: 0,
            at_lab: 0,
            in_analysis: 0,
            results_returned: 0,
            archived: 0,
            stored: 0,
            missing: 0,
            overdue_review: 0,
        }
    );
    const casesWithEvidence = new Set(evidence.map((item) => item.case_id).filter(Boolean));
    const pendingLabEvidence = evidence.filter((item) =>
        ["at_lab", "in_analysis", "submitted"].includes(normalizeStatus(item.custody_status))
    );
    const awaitingReview = evidence.filter((item) =>
        ["results_returned", "overdue_review"].includes(normalizeStatus(item.custody_status))
    );
    const evidenceSummary = {
        openCases: casesWithEvidence.size,
        total: evidence.length,
        newThisWeek: evidence.filter((item) => isThisWeek(evidenceDate(item))).length,
        awaitingReview: awaitingReview.length,
        labPending: pendingLabEvidence.length,
        missing: statusCounts.missing,
        criticalAlerts: evidence.filter(
            (item) =>
                item.is_sensitive ||
                ["missing", "overdue_review", "results_returned"].includes(normalizeStatus(item.custody_status))
        ).length,
    };
    const evidenceAlerts = [
        {
            title: "Evidence not submitted",
            value: statusCounts.collected,
            detail: "Collected items still waiting for formal submission or storage update.",
        },
        {
            title: "Lab results returned",
            value: statusCounts.results_returned,
            detail: "Items ready for supervisor or investigator review.",
        },
        {
            title: "Critical evidence added",
            value: evidence.filter((item) => item.is_sensitive).length,
            detail: "Sensitive or high-value items connected to active cases.",
        },
        {
            title: "Custody exception",
            value: statusCounts.missing + statusCounts.overdue_review,
            detail: "Missing evidence or overdue custody reviews requiring follow-up.",
        },
    ];
    const visibleEvidence = evidence.filter((item) =>
        statusFilter === "all" || normalizeStatus(item.custody_status) === statusFilter
    );

    const loadEvidence = async (caseFilter = filterCaseId) => {
        const data = await fetchEvidence(caseFilter);
        setEvidence(Array.isArray(data) ? data : []);
    };

    useEffect(() => {
        let isMounted = true;

        fetchEvidence("")
            .then((data) => {
                if (isMounted) {
                    setEvidence(Array.isArray(data) ? data : []);
                }
            })
            .catch((err) => console.error(err));

        return () => {
            isMounted = false;
        };
    }, []);

    const submitEvidence = async (e) => {
        e.preventDefault();

        const formData = new FormData();

        formData.append("case_id", caseId);
        formData.append("evidence_type", evidenceType);
        formData.append("description", description);
        formData.append("file", file);

        try {
            const data = await apiPostForm("/evidence/upload", formData);

            setMessage(data.message);
            setEvidenceType("");
            setDescription("");
            setFile(null);
            await loadEvidence(filterCaseId);
        } catch (err) {
            console.error(err);
            setMessage("Could not upload evidence.");
        }
    };

    const viewEvidence = async (evidenceId) => {
        try {
            const blob = await apiBlob(`/evidence/view/${evidenceId}`);
            const fileUrl = window.URL.createObjectURL(blob);
            window.open(fileUrl, "_blank");
        } catch (err) {
            console.error(err);
            setMessage(err.message || "Could not open evidence.");
        }
    };

    const loadEvidenceChain = async (evidenceId) => {
        try {
            const data = await apiGet(`/evidence/chain/${evidenceId}`);
            setEvidenceChains((prev) => ({
                ...prev,
                [evidenceId]: data,
            }));
        } catch (err) {
            console.error(err);
        }
    };

    const markEvidenceSensitive = async (evidenceId, isSensitive) => {
        try {
            await apiRequest(`/evidence/${evidenceId}/sensitive?is_sensitive=${isSensitive}`, {
                method: "PUT",
            });

            setEvidence(
                evidence.map((item) =>
                    item.evidence_id === evidenceId
                        ? { ...item, is_sensitive: isSensitive }
                        : item
                )
            );
        } catch (err) {
            console.error(err);
            alert("Could not update evidence sensitivity.");
        }
    };

    const updateCustodyForm = (evidenceId, field, value) => {
        setCustodyForms((current) => ({
            ...current,
            [evidenceId]: {
                action: "TRANSFERRED",
                from_holder: "",
                to_holder: "",
                location: "",
                lab_reference: "",
                available_at: "",
                details: "",
                ...(current[evidenceId] || {}),
                [field]: value,
            },
        }));
    };

    const submitCustodyEvent = async (e, item) => {
        e.preventDefault();

        const form = custodyForms[item.evidence_id] || {};
        const payload = {
            action: form.action || "TRANSFERRED",
            from_holder: form.from_holder || item.current_holder || "",
            to_holder: form.to_holder || "",
            location: form.location || "",
            lab_reference: form.lab_reference || "",
            available_at: form.available_at || null,
            details: form.details || "",
        };

        try {
            await apiPost(`/evidence/${item.evidence_id}/custody`, payload);

            setMessage("Evidence custody updated.");
            setCustodyForms((current) => ({
                ...current,
                [item.evidence_id]: {
                    action: "TRANSFERRED",
                    from_holder: "",
                    to_holder: "",
                    location: "",
                    lab_reference: "",
                    available_at: "",
                    details: "",
                },
            }));
            await loadEvidence(filterCaseId);
            await loadEvidenceChain(item.evidence_id);
        } catch (err) {
            console.error(err);
            setMessage(err.message || "Could not update evidence custody.");
        }
    };

    return (
        <div className="evidence-page">
            <div className="evidence-header">
                <h1>Evidence</h1>
            </div>

            <section className="evidence-command-strip" aria-label="Evidence command summary">
                <article>
                    <span>Open Cases</span>
                    <strong>{evidenceSummary.openCases}</strong>
                    <small>Cases with evidence activity</small>
                </article>
                <article>
                    <span>Evidence Items</span>
                    <strong>{evidenceSummary.total}</strong>
                    <small>Total items in Beacon</small>
                </article>
                <article>
                    <span>Pending Lab Results</span>
                    <strong>{evidenceSummary.labPending}</strong>
                    <small>Submitted or in analysis</small>
                </article>
                <article>
                    <span>Overdue Reviews</span>
                    <strong>{statusCounts.overdue_review}</strong>
                    <small>Need command follow-up</small>
                </article>
                <article>
                    <span>Critical Alerts</span>
                    <strong>{evidenceSummary.criticalAlerts}</strong>
                    <small>Returned, missing, or sensitive</small>
                </article>
            </section>

            <section className="evidence-dashboard-grid" aria-label="Evidence supervisor dashboard">
                <article className="evidence-panel">
                    <h2>Case-Level View</h2>
                    <div className="evidence-kpi-list">
                        <div>
                            <span>Total evidence items</span>
                            <strong>{evidenceSummary.total}</strong>
                        </div>
                        <div>
                            <span>New evidence this week</span>
                            <strong>{evidenceSummary.newThisWeek}</strong>
                        </div>
                        <div>
                            <span>Evidence awaiting review</span>
                            <strong>{evidenceSummary.awaitingReview}</strong>
                        </div>
                        <div>
                            <span>Lab requests pending</span>
                            <strong>{evidenceSummary.labPending}</strong>
                        </div>
                    </div>
                </article>

                <article className="evidence-panel">
                    <h2>Status Tracking</h2>
                    <div className="evidence-status-grid">
                        <div><span>Collected</span><strong>{statusCounts.collected}</strong></div>
                        <div><span>Submitted</span><strong>{statusCounts.submitted + statusCounts.at_lab}</strong></div>
                        <div><span>In Analysis</span><strong>{statusCounts.in_analysis}</strong></div>
                        <div><span>Returned</span><strong>{statusCounts.results_returned}</strong></div>
                        <div><span>Archived</span><strong>{statusCounts.archived}</strong></div>
                    </div>
                </article>

                <article className="evidence-panel evidence-alert-panel">
                    <h2>Supervisor Alerts</h2>
                    <div className="evidence-alert-list">
                        {evidenceAlerts.map((alert) => (
                            <div key={alert.title} className={alert.value > 0 ? "evidence-alert-item active" : "evidence-alert-item"}>
                                <strong>{alert.value}</strong>
                                <span>{alert.title}</span>
                                <small>{alert.detail}</small>
                            </div>
                        ))}
                    </div>
                </article>
            </section>

            <div className="evidence-layout">
                <section className="evidence-panel">
                    <h2>Upload Evidence</h2>

                    <form className="evidence-form" onSubmit={submitEvidence}>
                        <input
                            type="number"
                            placeholder="Case ID"
                            value={caseId}
                            onChange={(e) => setCaseId(e.target.value)}
                            required
                        />

                        <input
                            type="text"
                            placeholder="Evidence Type"
                            value={evidenceType}
                            onChange={(e) => setEvidenceType(e.target.value)}
                            required
                        />

                        <textarea
                            placeholder="Description"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                        />

                        <input
                            type="file"
                            onChange={(e) => setFile(e.target.files[0])}
                            required
                        />

                        <button type="submit">Upload Evidence</button>
                    </form>

                    {message && <p>{message}</p>}
                </section>

                <section className="evidence-panel">
                    <div className="evidence-registry-header">
                        <h2>Evidence Registry</h2>
                        <div className="evidence-filter">
                            <input
                                type="number"
                                placeholder="Filter by Case ID"
                                value={filterCaseId}
                                onChange={(e) => {
                                    setFilterCaseId(e.target.value);
                                    setVisibleEvidenceCount(2);
                                }}
                            />
                            <button onClick={() => loadEvidence(filterCaseId)}>
                                Search
                            </button>
                            <select
                                value={statusFilter}
                                onChange={(e) => {
                                    const nextStatus = e.target.value;
                                    setSearchParams(nextStatus === "all" ? {} : { status: nextStatus });
                                    setVisibleEvidenceCount(2);
                                }}
                            >
                                <option value="all">All statuses</option>
                                <option value="collected">Collected</option>
                                <option value="submitted">Submitted</option>
                                <option value="stored">In storage</option>
                                <option value="at_lab">At lab</option>
                                <option value="in_analysis">In analysis</option>
                                <option value="results_returned">Results returned</option>
                                <option value="archived">Archived</option>
                                <option value="missing">Missing</option>
                                <option value="overdue_review">Overdue review</option>
                            </select>
                            <button
                                onClick={() => {
                                    setFilterCaseId("");
                                    setSearchParams({});
                                    setVisibleEvidenceCount(2);
                                    loadEvidence("");
                                }}
                            >
                                Clear
                            </button>
                        </div>
                    </div>

                    {visibleEvidence.length === 0 ? (
                        <p>No evidence uploaded yet.</p>
                    ) : (
                        <div className="evidence-list">
                            {visibleEvidence.slice(0, visibleEvidenceCount).map((item) => (
                                <article key={item.evidence_id} className="evidence-card">
                                    <div className="evidence-card-topline">
                                        <strong>{item.file_name || "Unnamed file"}</strong>
                                        <span className={`evidence-status-indicator ${getEvidenceIndicator(item.custody_status)[1]}`}>
                                            {getEvidenceIndicator(item.custody_status)[0]}
                                        </span>
                                        {item.is_sensitive && <span className="sensitive-badge">Sensitive</span>}
                                    </div>

                                    <p>Case: {item.case_number || item.case_id}</p>
                                    {item.case_title && <p>Case title: {item.case_title}</p>}
                                    <p>Assigned investigator: {item.assigned_investigator || "Not recorded"}</p>
                                    <p>Type: {item.evidence_type}</p>
                                    <p>Collected by: {item.collected_by_name || item.current_holder || "Not recorded"}</p>
                                    <p>Status: {item.custody_status || "collected"}</p>
                                    <p>Current holder: {item.current_holder || "Not recorded"}</p>
                                    <p>Location: {item.evidence_location || "Not recorded"}</p>
                                    {item.lab_reference && <p>Lab reference: {item.lab_reference}</p>}
                                    {item.available_at && (
                                        <p>Available: {new Date(item.available_at).toLocaleString()}</p>
                                    )}
                                    <p>{item.description || "No description provided"}</p>

                                    <form
                                        className="evidence-custody-form"
                                        onSubmit={(e) => submitCustodyEvent(e, item)}
                                    >
                                        <select
                                            value={custodyForms[item.evidence_id]?.action || "TRANSFERRED"}
                                            onChange={(e) =>
                                                updateCustodyForm(item.evidence_id, "action", e.target.value)
                                            }
                                        >
                                            {custodyActions.map(([value, label]) => (
                                                <option key={value} value={value}>{label}</option>
                                            ))}
                                        </select>
                                        <input
                                            placeholder="From"
                                            value={custodyForms[item.evidence_id]?.from_holder || ""}
                                            onChange={(e) =>
                                                updateCustodyForm(item.evidence_id, "from_holder", e.target.value)
                                            }
                                        />
                                        <input
                                            placeholder="To / current holder"
                                            value={custodyForms[item.evidence_id]?.to_holder || ""}
                                            onChange={(e) =>
                                                updateCustodyForm(item.evidence_id, "to_holder", e.target.value)
                                            }
                                        />
                                        <input
                                            placeholder="Location"
                                            value={custodyForms[item.evidence_id]?.location || ""}
                                            onChange={(e) =>
                                                updateCustodyForm(item.evidence_id, "location", e.target.value)
                                            }
                                        />
                                        <input
                                            placeholder="Lab reference"
                                            value={custodyForms[item.evidence_id]?.lab_reference || ""}
                                            onChange={(e) =>
                                                updateCustodyForm(item.evidence_id, "lab_reference", e.target.value)
                                            }
                                        />
                                        <input
                                            type="datetime-local"
                                            value={custodyForms[item.evidence_id]?.available_at || ""}
                                            onChange={(e) =>
                                                updateCustodyForm(item.evidence_id, "available_at", e.target.value)
                                            }
                                        />
                                        <textarea
                                            placeholder="Discovery, analysis notes, transfer notes, or expected availability"
                                            value={custodyForms[item.evidence_id]?.details || ""}
                                            onChange={(e) =>
                                                updateCustodyForm(item.evidence_id, "details", e.target.value)
                                            }
                                        />
                                        <button type="submit">Record Custody Event</button>
                                    </form>

                                    <div className="evidence-actions">
                                        <button
                                            onClick={() => viewEvidence(item.evidence_id)}
                                        >
                                            Open File
                                        </button>
                                        <button
                                            onClick={() =>
                                                loadEvidenceChain(item.evidence_id)
                                            }
                                        >
                                            Chain of Custody
                                        </button>
                                        <button
                                            onClick={() =>
                                                markEvidenceSensitive(
                                                    item.evidence_id,
                                                    !item.is_sensitive
                                                )
                                            }
                                        >
                                            {item.is_sensitive
                                                ? "Unmark Sensitive"
                                                : "Mark Sensitive"}
                                        </button>
                                    </div>

                                    {evidenceChains[item.evidence_id]?.map((event) => (
                                        <div
                                            key={event.chain_id}
                                            className="evidence-chain-item"
                                        >
                                            <p><strong>Action:</strong> {event.action}</p>
                                            <p>
                                                <strong>From / To:</strong> {event.from_holder || "Not recorded"} to {event.to_holder || "Not recorded"}
                                            </p>
                                            <p><strong>Location:</strong> {event.location || "Not recorded"}</p>
                                            <p><strong>Details:</strong> {event.details}</p>
                                            {event.available_at && (
                                                <p><strong>Available:</strong> {new Date(event.available_at).toLocaleString()}</p>
                                            )}
                                            <p><strong>Date:</strong> {new Date(event.created_at).toLocaleString()}</p>
                                        </div>
                                    ))}
                                </article>
                            ))}
                            <ShowMoreControls
                                total={visibleEvidence.length}
                                visible={visibleEvidenceCount}
                                noun="evidence items"
                                onShowMore={() => {
                                    setVisibleEvidenceCount((current) =>
                                        Math.min(current + 4, visibleEvidence.length)
                                    );
                                }}
                                onShowAll={() => setVisibleEvidenceCount(visibleEvidence.length)}
                                onShowFewer={() => setVisibleEvidenceCount(2)}
                            />
                        </div>
                    )}
                </section>
            </div>
        </div>
    );
}

export default EvidenceUpload;
