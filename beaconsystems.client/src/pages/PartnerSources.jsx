import React, { useEffect, useMemo, useState } from "react";

const sourceTypes = [
    "hospital",
    "medical_examiner",
    "crime_lab",
    "transportation",
    "camera",
    "toll",
    "cell_provider",
    "social_media",
    "fusion_center",
    "prosecutor",
    "court",
    "social_services",
    "family_portal",
    "ngo",
    "other",
];

const emptySourceForm = {
    name: "",
    source_type: "hospital",
    api_url: "",
    description: "",
};

const emptyIntakeForm = {
    integration_source_id: "",
    record_type: "partner_lead",
    external_id: "",
    subject_name: "",
    location: "",
    summary: "",
    raw_data: "",
};

const legalAuthorityOptions = [
    { value: "consent", label: "Consent" },
    { value: "subpoena", label: "Subpoena" },
    { value: "search_warrant", label: "Search warrant" },
    { value: "court_order", label: "Court order" },
    { value: "wiretap_order", label: "Wiretap order" },
    { value: "emergency_disclosure", label: "Emergency disclosure" },
    { value: "partner_agreement", label: "Approved partner agreement" },
    { value: "other", label: "Other approved authority" },
];

const partnerCapabilityRows = [
    ["Hospitals / Mental Health", "Encounter checks, admission inquiries, emergency disclosure requests", "Legal access required"],
    ["Medical Examiners", "Morgue comparison, decedent identification, fingerprints, dental, DNA", "Case-linked request"],
    ["Crime Labs", "DNA, fingerprints, toxicology, evidence analysis", "Submission tracking"],
    ["Missing Person Organizations", "NamUs, NCMEC, advocacy partner coordination", "Approved referral"],
    ["Courts / Prosecutors", "Warrants, subpoenas, court orders, filing packets", "Judicial workflow"],
    ["Fusion Centers", "Intelligence bulletins, regional leads, cross-jurisdiction coordination", "Supervisor review"],
    ["Family Portal", "Controlled updates, tips, documents, consent-based information", "Limited access"],
];

const authHeaders = (includeJson = false) => {
    const headers = {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
    };

    if (includeJson) {
        headers["Content-Type"] = "application/json";
    }

    return headers;
};

const fetchPartnerWorkspace = async () => {
    const [sourcesResponse, recordsResponse, intakeResponse] = await Promise.all([
        fetch("http://127.0.0.1:8000/integrations/", {
            headers: authHeaders(),
        }),
        fetch("http://127.0.0.1:8000/external-records/", {
            headers: authHeaders(),
        }),
        fetch("http://127.0.0.1:8000/partner-intake/", {
            headers: authHeaders(),
        }),
    ]);

    if (!sourcesResponse.ok) {
        throw new Error("Failed to load partner sources");
    }

    const sourcesData = await sourcesResponse.json();
    const recordsData = recordsResponse.ok ? await recordsResponse.json() : [];
    const intakeData = intakeResponse.ok ? await intakeResponse.json() : [];

    return {
        sources: Array.isArray(sourcesData) ? sourcesData : [],
        externalRecords: Array.isArray(recordsData) ? recordsData : [],
        intakeRecords: Array.isArray(intakeData) ? intakeData : [],
    };
};

function PartnerSources() {
    const [sources, setSources] = useState([]);
    const [externalRecords, setExternalRecords] = useState([]);
    const [intakeRecords, setIntakeRecords] = useState([]);
    const [message, setMessage] = useState("");
    const [sourceForm, setSourceForm] = useState(emptySourceForm);
    const [intakeForm, setIntakeForm] = useState(emptyIntakeForm);
    const [reviewForms, setReviewForms] = useState({});
    const [expandedLists, setExpandedLists] = useState({});
    const [sourceSearch, setSourceSearch] = useState("");
    const [sourceStatusFilter, setSourceStatusFilter] = useState("all");
    const [sourceTypeFilter, setSourceTypeFilter] = useState("all");
    const role = localStorage.getItem("role");
    const canCreatePartnerSource = role === "admin";
    const canReceivePartnerData = role === "admin" || role === "agency_admin";
    const showSupervisorPartnerView = !canCreatePartnerSource;
    const visibleItems = (key, items) =>
        (items || []).slice(0, expandedLists[key] ? 6 : 2);
    const renderListToggle = (key, count, label) => count > 2 ? (
        <button
            type="button"
            className="list-toggle-button"
            onClick={() =>
                setExpandedLists((current) => ({
                    ...current,
                    [key]: !current[key],
                }))
            }
        >
            {expandedLists[key] ? "Show fewer" : `Show ${Math.min(4, count - 2)} more ${label}`}
        </button>
    ) : null;

    const approvedSources = useMemo(
        () =>
            sources.filter(
                (source) => source.status === "approved" && source.is_active
            ),
        [sources]
    );
    const partnerSummary = useMemo(() => {
        const pendingSources = sources.filter((source) => source.status === "pending").length;
        const suspendedSources = sources.filter(
            (source) => source.status === "suspended" || source.status === "revoked"
        ).length;

        return [
            ["Approved Partners", approvedSources.length],
            ["Pending Data Reviews", intakeRecords.length],
            ["Linked External Records", externalRecords.length],
            ["Suspended / Revoked", suspendedSources],
            ["Pending Approvals", pendingSources],
        ];
    }, [approvedSources.length, externalRecords.length, intakeRecords.length, sources]);
    const filteredSources = useMemo(() => {
        const searchTerm = sourceSearch.trim().toLowerCase();

        return sources
            .filter((source) => {
                const searchText = [
                    source.name,
                    source.source_type,
                    source.status,
                    source.description,
                    source.api_url,
                ]
                    .filter(Boolean)
                    .join(" ")
                    .toLowerCase();
                const matchesSearch = !searchTerm || searchText.includes(searchTerm);
                const matchesStatus = sourceStatusFilter === "all" || source.status === sourceStatusFilter;
                const matchesType = sourceTypeFilter === "all" || source.source_type === sourceTypeFilter;

                return matchesSearch && matchesStatus && matchesType;
            })
            .sort((firstSource, secondSource) =>
                (firstSource.name || "").localeCompare(secondSource.name || "")
            );
    }, [sourceSearch, sourceStatusFilter, sourceTypeFilter, sources]);

    const sourceNameById = useMemo(() => {
        return sources.reduce((lookup, source) => {
            lookup[source.id] = source.name;
            return lookup;
        }, {});
    }, [sources]);

    const loadPartnerWorkspace = async () => {
        const workspace = await fetchPartnerWorkspace();

        setSources(workspace.sources);
        setExternalRecords(workspace.externalRecords);
        setIntakeRecords(workspace.intakeRecords);
    };

    useEffect(() => {
        let isMounted = true;

        fetchPartnerWorkspace()
            .then((workspace) => {
                if (!isMounted) {
                    return;
                }

                setSources(workspace.sources);
                setExternalRecords(workspace.externalRecords);
                setIntakeRecords(workspace.intakeRecords);
            })
            .catch((err) => {
                console.error(err);

                if (isMounted) {
                    setMessage("Could not load partner workspace.");
                }
            });

        return () => {
            isMounted = false;
        };
    }, []);

    const updateSourceForm = (e) => {
        setSourceForm({
            ...sourceForm,
            [e.target.name]: e.target.value,
        });
    };

    const updateIntakeForm = (e) => {
        setIntakeForm({
            ...intakeForm,
            [e.target.name]: e.target.value,
        });
    };

    const updateReviewForm = (intakeId, field, value) => {
        setReviewForms({
            ...reviewForms,
            [intakeId]: {
                ...reviewForms[intakeId],
                [field]: value,
            },
        });
    };

    const submitSource = async (e) => {
        e.preventDefault();

        try {
            const response = await fetch("http://127.0.0.1:8000/integrations/", {
                method: "POST",
                headers: authHeaders(true),
                body: JSON.stringify(sourceForm),
            });

            if (!response.ok) {
                throw new Error("Could not create partner source");
            }

            setMessage("Partner source created and marked pending.");
            setSourceForm(emptySourceForm);
            await loadPartnerWorkspace();
        } catch (err) {
            console.error(err);
            setMessage("Could not create partner source.");
        }
    };

    const submitPartnerData = async (e) => {
        e.preventDefault();

        try {
            const payload = {
                ...intakeForm,
                integration_source_id: Number(intakeForm.integration_source_id),
                raw_data: intakeForm.raw_data
                    ? JSON.parse(intakeForm.raw_data)
                    : null,
            };

            const response = await fetch("http://127.0.0.1:8000/partner-intake/", {
                method: "POST",
                headers: authHeaders(true),
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Could not receive partner data");
            }

            setMessage("Partner data received and added to investigator review.");
            setIntakeForm(emptyIntakeForm);
            await loadPartnerWorkspace();
        } catch (err) {
            console.error(err);
            setMessage(
                err instanceof SyntaxError
                    ? "Raw data must be valid JSON."
                    : err.message || "Could not receive partner data."
            );
        }
    };

    const updateSource = async (sourceId, updates) => {
        try {
            const response = await fetch(
                `http://127.0.0.1:8000/integrations/${sourceId}`,
                {
                    method: "PUT",
                    headers: authHeaders(true),
                    body: JSON.stringify(updates),
                }
            );

            if (!response.ok) {
                throw new Error("Could not update partner source");
            }

            await loadPartnerWorkspace();
        } catch (err) {
            console.error(err);
            alert("Could not update partner source.");
        }
    };

    const attachToCase = async (record) => {
        const review = reviewForms[record.intake_id] || {};
        const caseId = review.case_id || record.suggested_case_id;
        const personId = review.person_id || record.suggested_person_id;

        if (!caseId) {
            setMessage("Choose a case before adding partner data to the case.");
            return;
        }

        if (!review.legal_authority_type) {
            setMessage("Select legal authority before adding partner data to a case.");
            return;
        }

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/partner-intake/${record.intake_id}/attach`,
                {
                    method: "PUT",
                    headers: authHeaders(true),
                    body: JSON.stringify({
                        case_id: Number(caseId),
                        person_id: personId ? Number(personId) : null,
                        review_notes: review.review_notes || null,
                        legal_authority_type: review.legal_authority_type,
                        legal_authority_reference:
                            review.legal_authority_reference || null,
                        legal_authority_notes:
                            review.legal_authority_notes || null,
                    }),
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Could not attach partner data");
            }

            setMessage("Partner data attached to the case and logged.");
            await loadPartnerWorkspace();
        } catch (err) {
            console.error(err);
            setMessage(err.message || "Could not attach partner data.");
        }
    };

    const dismissRecord = async (intakeId) => {
        const review = reviewForms[intakeId] || {};

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/partner-intake/${intakeId}/dismiss`,
                {
                    method: "PUT",
                    headers: authHeaders(true),
                    body: JSON.stringify({
                        review_notes: review.review_notes || "Dismissed after review",
                    }),
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Could not dismiss partner data");
            }

            setMessage("Partner data dismissed and logged.");
            await loadPartnerWorkspace();
        } catch (err) {
            console.error(err);
            setMessage(err.message || "Could not dismiss partner data.");
        }
    };

    return (
        <div className="partner-page">
            <div className="partner-header">
                <h1>Partners</h1>
            </div>

            {message && <p className="alert-banner">{message}</p>}

            <div className="partner-workspace-layout">
                {showSupervisorPartnerView && (
                    <section className="partner-panel partner-summary-panel">
                        <div className="partner-intake-panel-header">
                            <span>Partner Network</span>
                            <strong>Operational Visibility</strong>
                        </div>

                        <div className="partner-summary-grid">
                            {partnerSummary.map(([label, value]) => (
                                <span key={label}>
                                    {label}
                                    <strong>{value}</strong>
                                </span>
                            ))}
                        </div>
                    </section>
                )}

                {showSupervisorPartnerView && (
                    <section className="partner-panel partner-directory-panel">
                        <div className="partner-intake-panel-header">
                            <span>Directory</span>
                            <strong>Approved Collaboration Partners</strong>
                        </div>

                        {approvedSources.length === 0 ? (
                            <p>No approved partner sources are active yet.</p>
                        ) : (
                            <div className="partner-list">
                                {visibleItems("approvedSources", approvedSources).map((source) => (
                                    <article key={source.id} className="partner-card">
                                        <div className="partner-topline">
                                            <strong>{source.name}</strong>
                                            <span className={`request-status ${source.status}`}>
                                                {source.status}
                                            </span>
                                        </div>
                                        <p>{source.source_type.replace("_", " ")}</p>
                                        <p>{source.description || "No agreement notes recorded."}</p>
                                        <p>{source.api_url || "No secure endpoint registered."}</p>
                                    </article>
                                ))}
                                {renderListToggle("approvedSources", approvedSources.length, "partners")}
                            </div>
                        )}
                    </section>
                )}

                {showSupervisorPartnerView && (
                    <section className="partner-panel partner-capability-panel">
                        <div className="partner-intake-panel-header">
                            <span>Collaboration</span>
                            <strong>Missing Persons Partner Capabilities</strong>
                        </div>

                        <div className="partner-capability-list">
                            {partnerCapabilityRows.map(([name, capability, guardrail]) => (
                                <article key={name}>
                                    <strong>{name}</strong>
                                    <p>{capability}</p>
                                    <span>{guardrail}</span>
                                </article>
                            ))}
                        </div>
                    </section>
                )}

                {canReceivePartnerData && (
                    <section className="partner-intake-panel">
                        <div className="partner-intake-panel-header">
                            <span>Partner feed</span>
                            <strong>Receive Data</strong>
                        </div>

                        <form className="partner-intake-form" onSubmit={submitPartnerData}>
                            <select
                                name="integration_source_id"
                                value={intakeForm.integration_source_id}
                                onChange={updateIntakeForm}
                                required
                            >
                                <option value="">Approved partner source</option>
                                {approvedSources.map((source) => (
                                    <option key={source.id} value={source.id}>
                                        {source.name}
                                    </option>
                                ))}
                            </select>

                            <input
                                name="record_type"
                                placeholder="Record type"
                                value={intakeForm.record_type}
                                onChange={updateIntakeForm}
                                required
                            />

                            <input
                                name="external_id"
                                placeholder="Partner reference ID"
                                value={intakeForm.external_id}
                                onChange={updateIntakeForm}
                            />

                            <input
                                name="subject_name"
                                placeholder="Subject name"
                                value={intakeForm.subject_name}
                                onChange={updateIntakeForm}
                            />

                            <input
                                name="location"
                                placeholder="Location"
                                value={intakeForm.location}
                                onChange={updateIntakeForm}
                            />

                            <textarea
                                name="summary"
                                placeholder="Summary for investigator review"
                                value={intakeForm.summary}
                                onChange={updateIntakeForm}
                                required
                            />

                            <textarea
                                name="raw_data"
                                placeholder='Optional raw JSON, for example {"source":"camera","confidence":0.91}'
                                value={intakeForm.raw_data}
                                onChange={updateIntakeForm}
                            />

                            <button type="submit">Add to Review Queue</button>
                        </form>
                    </section>
                )}

                <section className="partner-intake-panel partner-intake-review-panel">
                    <div className="partner-intake-panel-header">
                        <span>Investigator review</span>
                        <strong>{intakeRecords.length} pending</strong>
                    </div>

                    {intakeRecords.length === 0 ? (
                        <p>No partner data waiting for review.</p>
                    ) : (
                        <div className="partner-intake-list">
                            {visibleItems("intakeRecords", intakeRecords).map((record) => (
                                <article
                                    key={record.intake_id}
                                    className="partner-intake-card"
                                >
                                    <div className="partner-intake-card-topline">
                                        <div>
                                            <strong>
                                                {sourceNameById[record.integration_source_id] ||
                                                    "Partner Source"}
                                            </strong>
                                            <span>{record.record_type}</span>
                                        </div>
                                        <span className={`request-status ${record.status}`}>
                                            {record.status.replace("_", " ")}
                                        </span>
                                    </div>

                                    <h3>{record.subject_name || "Unmatched subject"}</h3>
                                    <p>{record.summary}</p>

                                    {record.suggested_case_id ? (
                                        <div className="partner-match-suggestion">
                                            <strong>
                                                Suggested match: Case {record.suggested_case_id}
                                            </strong>
                                            <span>
                                                {record.match_score || 0}% confidence
                                                {record.match_case_status
                                                    ? ` - ${record.match_case_status}`
                                                    : ""}
                                            </span>
                                            <p>{record.match_reason}</p>
                                        </div>
                                    ) : (
                                        <div className="partner-match-suggestion unmatched">
                                            <strong>No strong case match</strong>
                                            <span>Investigator review required</span>
                                        </div>
                                    )}

                                    <dl className="partner-intake-details">
                                        <div>
                                            <dt>Location</dt>
                                            <dd>{record.location || "Not provided"}</dd>
                                        </div>
                                        <div>
                                            <dt>External ID</dt>
                                            <dd>{record.external_id || "Not provided"}</dd>
                                        </div>
                                    </dl>

                                    <div className="partner-intake-review-form">
                                        <input
                                            type="number"
                                            placeholder="Case ID"
                                            value={
                                                reviewForms[record.intake_id]?.case_id ||
                                                record.suggested_case_id ||
                                                ""
                                            }
                                            onChange={(e) =>
                                                updateReviewForm(
                                                    record.intake_id,
                                                    "case_id",
                                                    e.target.value
                                                )
                                            }
                                        />

                                        <input
                                            type="number"
                                            placeholder="Person ID (optional)"
                                            value={
                                                reviewForms[record.intake_id]?.person_id ||
                                                record.suggested_person_id ||
                                                ""
                                            }
                                            onChange={(e) =>
                                                updateReviewForm(
                                                    record.intake_id,
                                                    "person_id",
                                                    e.target.value
                                                )
                                            }
                                        />

                                        <select
                                            value={
                                                reviewForms[record.intake_id]
                                                    ?.legal_authority_type || ""
                                            }
                                            onChange={(e) =>
                                                updateReviewForm(
                                                    record.intake_id,
                                                    "legal_authority_type",
                                                    e.target.value
                                                )
                                            }
                                            required
                                        >
                                            <option value="">Legal authority</option>
                                            {legalAuthorityOptions.map((option) => (
                                                <option
                                                    key={option.value}
                                                    value={option.value}
                                                >
                                                    {option.label}
                                                </option>
                                            ))}
                                        </select>

                                        <input
                                            placeholder="Authority reference"
                                            value={
                                                reviewForms[record.intake_id]
                                                    ?.legal_authority_reference || ""
                                            }
                                            onChange={(e) =>
                                                updateReviewForm(
                                                    record.intake_id,
                                                    "legal_authority_reference",
                                                    e.target.value
                                                )
                                            }
                                        />

                                        <textarea
                                            placeholder="Review notes"
                                            value={
                                                reviewForms[record.intake_id]?.review_notes || ""
                                            }
                                            onChange={(e) =>
                                                updateReviewForm(
                                                    record.intake_id,
                                                    "review_notes",
                                                    e.target.value
                                                )
                                            }
                                        />

                                        <textarea
                                            placeholder="Legal authority notes"
                                            value={
                                                reviewForms[record.intake_id]
                                                    ?.legal_authority_notes || ""
                                            }
                                            onChange={(e) =>
                                                updateReviewForm(
                                                    record.intake_id,
                                                    "legal_authority_notes",
                                                    e.target.value
                                                )
                                            }
                                        />
                                    </div>

                                    <div className="partner-intake-actions">
                                        <button
                                            type="button"
                                            onClick={() => attachToCase(record)}
                                        >
                                            Add to Case
                                        </button>
                                        <button
                                            type="button"
                                            className="secondary-button"
                                            onClick={() => dismissRecord(record.intake_id)}
                                        >
                                            Dismiss
                                        </button>
                                    </div>
                                </article>
                            ))}
                            {renderListToggle("intakeRecords", intakeRecords.length, "records")}
                        </div>
                    )}
                </section>

                {canCreatePartnerSource && (
                    <section className="partner-panel">
                        <h2>Source Registry</h2>
                        <div className="partner-source-controls">
                            <input
                                type="search"
                                placeholder="Search partners"
                                value={sourceSearch}
                                onChange={(event) => setSourceSearch(event.target.value)}
                            />
                            <select
                                value={sourceStatusFilter}
                                onChange={(event) => setSourceStatusFilter(event.target.value)}
                            >
                                <option value="all">All statuses</option>
                                <option value="pending">Pending</option>
                                <option value="approved">Approved</option>
                                <option value="suspended">Suspended</option>
                                <option value="revoked">Revoked</option>
                                <option value="denied">Denied</option>
                            </select>
                            <select
                                value={sourceTypeFilter}
                                onChange={(event) => setSourceTypeFilter(event.target.value)}
                            >
                                <option value="all">All types</option>
                                {sourceTypes.map((type) => (
                                    <option key={type} value={type}>
                                        {type.replace("_", " ")}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {filteredSources.length === 0 ? (
                            <p>No partner sources match the current filters.</p>
                        ) : (
                            <div className="partner-list">
                                {filteredSources.map((source) => {
                                    const recordCount = externalRecords.filter(
                                        (record) =>
                                            record.integration_source_id === source.id
                                    ).length;

                                    return (
                                        <article key={source.id} className="partner-card">
                                            <div className="partner-topline">
                                                <strong>{source.name}</strong>
                                                <span className={`request-status ${source.status}`}>
                                                    {source.status}
                                                </span>
                                            </div>

                                            <p>{source.source_type.replace("_", " ")}</p>
                                            <p>{source.description || "No description provided"}</p>
                                            <p>{source.api_url || "No API URL registered"}</p>
                                            <p>
                                                {source.is_active
                                                    ? "Active for approved use"
                                                    : "Inactive until approved"}
                                            </p>
                                            <p>{recordCount} external records linked</p>

                                            <div className="partner-actions">
                                                <button
                                                    onClick={() =>
                                                        updateSource(source.id, {
                                                            status: "approved",
                                                            is_active: true,
                                                        })
                                                    }
                                                >
                                                    Approve
                                                </button>
                                                <button
                                                    onClick={() =>
                                                        updateSource(source.id, {
                                                            status: "suspended",
                                                            is_active: false,
                                                        })
                                                    }
                                                >
                                                    Suspend
                                                </button>
                                                <button
                                                    onClick={() =>
                                                        updateSource(source.id, {
                                                            status: "revoked",
                                                            is_active: false,
                                                        })
                                                    }
                                                >
                                                    Revoke
                                                </button>
                                            </div>
                                        </article>
                                    );
                                })}
                            </div>
                        )}
                    </section>
                )}

                {canCreatePartnerSource && (
                    <section className="partner-panel">
                        <h2>Add Partner Source</h2>

                        <form className="partner-form" onSubmit={submitSource}>
                            <input
                                name="name"
                                placeholder="Partner name"
                                value={sourceForm.name}
                                onChange={updateSourceForm}
                                required
                            />

                            <select
                                name="source_type"
                                value={sourceForm.source_type}
                                onChange={updateSourceForm}
                            >
                                {sourceTypes.map((type) => (
                                    <option key={type} value={type}>
                                        {type.replace("_", " ")}
                                    </option>
                                ))}
                            </select>

                            <input
                                name="api_url"
                                placeholder="Approved API URL or intake endpoint"
                                value={sourceForm.api_url}
                                onChange={updateSourceForm}
                            />

                            <textarea
                                name="description"
                                placeholder="Agreement notes, coverage area, data types, and legal limits"
                                value={sourceForm.description}
                                onChange={updateSourceForm}
                            />

                            <button type="submit">Create Source</button>
                        </form>
                    </section>
                )}
            </div>
        </div>
    );
}

export default PartnerSources;
