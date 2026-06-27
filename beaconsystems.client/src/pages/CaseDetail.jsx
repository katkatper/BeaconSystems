import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import SightingMap from "./SightingMap.jsx";
import EscapeRouteAnalysis from "./EscapeRouteAnalysis.jsx";

function CaseDetail() {
    const { id } = useParams();

    const [caseItem, setCaseItem] = useState(null);
    const [sightings, setSightings] = useState([]);
    const [externalRecords, setExternalRecords] = useState([]);
    const [error, setError] = useState("");
    const [sightingMessage, setSightingMessage] = useState("");
    const [person, setPerson] = useState(null);
    const [timelineEvents, setTimelineEvents] = useState([]);
    const [evidence, setEvidence] = useState([]);
    const [evidenceChains, setEvidenceChains] = useState({});
    const [selectedExternalRecord, setSelectedExternalRecord] = useState(null);
    const [showSightingForm, setShowSightingForm] = useState(false);
    const [agencyExchanges, setAgencyExchanges] = useState([]);
    const [selectedExternalRequest, setSelectedExternalRequest] = useState(null);
    const [activeTab, setActiveTab] = useState("overview");
    const [associateForm, setAssociateForm] = useState({
        name: "",
        relationship: "",
        address: "",
        latitude: "",
        longitude: "",
        notes: "",
    });
    const [associateMessage, setAssociateMessage] = useState("");

    const [sightingForm, setSightingForm] = useState({
        location: "",
        latitude: "",
        longitude: "",
        description: "",
        confidence_score: "",
    });

    useEffect(() => {
        const token = localStorage.getItem("token");
        let isMounted = true;

        const authHeaders = {
            Authorization: `Bearer ${token}`,
        };

        const loadCaseDetail = async () => {
            try {
                const caseResponse = await fetch(`http://127.0.0.1:8000/cases/${id}`, {
                    headers: authHeaders,
                });

                if (!caseResponse.ok) {
                    throw new Error("Failed to load case");
                }

                const caseData = await caseResponse.json();

                if (!isMounted) return;
                setCaseItem(caseData);

                const [
                    sightingsResponse,
                    timelineResponse,
                    evidenceResponse,
                    personResponse,
                    externalRecordsResponse,
                    agencyExchangesResponse,
                ] = await Promise.all([
                    fetch(`http://127.0.0.1:8000/sightings/?case_id=${id}`, {
                        headers: authHeaders,
                    }),
                    fetch(`http://127.0.0.1:8000/timeline-events/?case_id=${id}`),
                    fetch(`http://127.0.0.1:8000/evidence/case/${id}`, {
                        headers: authHeaders,
                    }),
                    fetch(`http://127.0.0.1:8000/persons/${caseData.person_id}`, {
                        headers: authHeaders,
                    }),
                    fetch(
                        `http://127.0.0.1:8000/external-records/?person_id=${caseData.person_id}`,
                        { headers: authHeaders }
                    ),
                    fetch(`http://127.0.0.1:8000/agency-exchanges/?case_id=${id}`, {
                        headers: authHeaders,
                    }),
                ]);

                const [
                    sightingsData,
                    timelineData,
                    evidenceData,
                    personData,
                    externalRecordsData,
                    agencyExchangesData,
                ] = await Promise.all([
                    sightingsResponse.ok ? sightingsResponse.json() : [],
                    timelineResponse.ok ? timelineResponse.json() : [],
                    evidenceResponse.ok ? evidenceResponse.json() : [],
                    personResponse.ok ? personResponse.json() : null,
                    externalRecordsResponse.ok ? externalRecordsResponse.json() : [],
                    agencyExchangesResponse.ok ? agencyExchangesResponse.json() : [],
                ]);

                if (!isMounted) return;

                setSightings(Array.isArray(sightingsData) ? sightingsData : []);
                setTimelineEvents(Array.isArray(timelineData) ? timelineData : []);
                setEvidence(Array.isArray(evidenceData) ? evidenceData : []);
                setPerson(personData);
                setExternalRecords(
                    Array.isArray(externalRecordsData) ? externalRecordsData : []
                );
                setAgencyExchanges(
                    Array.isArray(agencyExchangesData) ? agencyExchangesData : []
                );
            } catch (err) {
                console.error(err);
                if (isMounted) {
                    setError("Could not load case details.");
                }
            }
        };

        loadCaseDetail();

        return () => {
            isMounted = false;
        };
    }, [id]);

    const handleSightingChange = (e) => {
        setSightingForm({
            ...sightingForm,
            [e.target.name]: e.target.value,
        });
    };

    const handleAssociateChange = (e) => {
        setAssociateForm({
            ...associateForm,
            [e.target.name]: e.target.value,
        });
    };

    const submitSighting = async (e) => {
        e.preventDefault();

        const token = localStorage.getItem("token");

        try {
            const payload = {
                case_id: Number(id),
                person_id: caseItem.person_id,
                location: sightingForm.location,
                latitude: sightingForm.latitude ? Number(sightingForm.latitude) : null,
                longitude: sightingForm.longitude ? Number(sightingForm.longitude) : null,
                description: sightingForm.description,
                confidence_score: sightingForm.confidence_score
                    ? Number(sightingForm.confidence_score)
                    : null,
                image_url: null,
            };

            const response = await fetch("http://127.0.0.1:8000/sightings/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) throw new Error("Failed to add sighting");

            const data = await response.json();

            setSightings([
                ...sightings,
                {
                    sighting_id: data.sighting_id,
                    ...payload,
                    created_at: new Date().toISOString(),
                },
            ]);

            setSightingMessage("Sighting added successfully.");
            setSightingForm({
                location: "",
                latitude: "",
                longitude: "",
                description: "",
                confidence_score: "",
            });
        } catch (err) {
            console.error(err);
            setSightingMessage("Could not add sighting.");
        }
    };

    const submitAssociate = async (e) => {
        e.preventDefault();

        if (!person?.person_id) {
            setAssociateMessage("Missing person profile is not loaded yet.");
            return;
        }

        const token = localStorage.getItem("token");
        const nextAssociate = {
            id: `associate-${Date.now()}`,
            name: associateForm.name || "Known associate",
            relationship: associateForm.relationship || "Not recorded",
            address: associateForm.address || "Address not recorded",
            latitude: associateForm.latitude,
            longitude: associateForm.longitude,
            notes: associateForm.notes,
        };
        const nextAssociates = [...associates, nextAssociate];

        try {
            const response = await fetch(`http://127.0.0.1:8000/persons/${person.person_id}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    known_associates: JSON.stringify(nextAssociates),
                }),
            });

            if (!response.ok) throw new Error("Failed to save associate");

            setPerson({
                ...person,
                known_associates: JSON.stringify(nextAssociates),
            });
            setAssociateForm({
                name: "",
                relationship: "",
                address: "",
                latitude: "",
                longitude: "",
                notes: "",
            });
            setAssociateMessage("Associate added to this case profile.");
        } catch (err) {
            console.error(err);
            setAssociateMessage("Could not save associate.");
        }
    };

    const loadEvidenceChain = async (evidenceId) => {
        const token = localStorage.getItem("token");

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/evidence/chain/${evidenceId}`,
                {
                    headers: { Authorization: `Bearer ${token}` },
                }
            );

            if (!response.ok) throw new Error("Failed to load chain");

            const data = await response.json();
            setEvidenceChains((prev) => ({
                ...prev,
                [evidenceId]: data,
            }));
        } catch (err) {
            console.error(err);
        }
    };

    const viewEvidence = async (evidenceId) => {
        const token = localStorage.getItem("token");

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/evidence/view/${evidenceId}`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                throw new Error("Could not open evidence");
            }

            const blob = await response.blob();
            const fileUrl = window.URL.createObjectURL(blob);
            window.open(fileUrl, "_blank");
        } catch (err) {
            console.error(err);
            alert("Could not open evidence.");
        }
    };

    const markEvidenceSensitive = async (evidenceId, isSensitive) => {
        const token = localStorage.getItem("token");

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/evidence/${evidenceId}/sensitive?is_sensitive=${isSensitive}`,
                {
                    method: "PUT",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                throw new Error("Could not update sensitivity");
            }

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

    if (error) return <p>{error}</p>;

    if (!caseItem) return <p>Loading case details...</p>;

    const sortedSightings = [...sightings].sort(
        (a, b) =>
            new Date(a.sighting_time || a.created_at) -
            new Date(b.sighting_time || b.created_at)
    );

    const getExternalRecordName = (record) => {
        if (!record.record_type) return "External Record";
        return record.record_type
            .replace(/_/g, " ")
            .replace(/\b\w/g, (letter) => letter.toUpperCase());
    };
    const parseAssociates = () => {
        const raw = person?.known_associates || person?.addresses || "";

        if (!raw.trim()) return [];

        try {
            const parsed = JSON.parse(raw);
            const entries = Array.isArray(parsed) ? parsed : [parsed];

            return entries.map((entry, index) => ({
                id: entry.id || `associate-${index}`,
                name: entry.name || entry.associate || `Known associate ${index + 1}`,
                relationship: entry.relationship || entry.type || "Not recorded",
                address: entry.address || entry.location || "Address recorded",
                latitude: entry.latitude ?? entry.lat ?? "",
                longitude: entry.longitude ?? entry.lng ?? entry.lon ?? "",
                notes: entry.notes || "",
            }));
        } catch {
            return raw
                .split(";")
                .map((entry, index) => {
                    const parts = entry.split("|").map((part) => part.trim());
                    return {
                        id: `associate-${index}`,
                        name: parts[0] || `Known associate ${index + 1}`,
                        address: parts[1] || parts[0] || "Address recorded",
                        relationship: parts[2] || "Not recorded",
                        latitude: parts[3],
                        longitude: parts[4],
                        notes: parts[5] || "",
                    };
                });
        }
    };
    const personName = person
        ? `${person.first_name || ""} ${person.last_name || ""}`.trim()
        : "Missing Person";
    const associates = parseAssociates();
    const associateLocations = associates.filter((entry) => entry.latitude && entry.longitude);
    const caseTabs = [
        ["overview", "Overview"],
        ["timeline", "Timeline"],
        ["escapeRoutes", "Escape Routes"],
        ["sightings", "Sightings"],
        ["evidence", "Evidence"],
        ["associates", "Associates"],
        ["leads", "Leads"],
        ["intelligence", "Intelligence"],
        ["externalRequests", "External Requests"],
        ["documents", "Documents"],
        ["audit", "Audit Log"],
    ];
    const intelligenceProfileItems = person
        ? [
            ["Associates", person.known_associates || "No known associates recorded."],
            ["Gang Affiliations", person.gang_affiliations || "No gang affiliations recorded."],
            ["Vehicles", person.vehicles || "No vehicle intelligence recorded."],
            ["Addresses", person.addresses || person.last_seen_location || "No address intelligence recorded."],
            ["Tips", person.tips || `${externalRecords.length} external records and ${sortedSightings.length} sightings available for review.`],
            ["Sightings", sortedSightings.length ? `${sortedSightings.length} sightings linked to this case.` : "No sightings linked yet."],
            ["Patterns", person.patterns || "No movement or contact patterns recorded."],
        ]
        : [];
    const statusLabel = (status) =>
        String(status || "pending")
            .replace(/_/g, " ")
            .replace(/\b\w/g, (letter) => letter.toUpperCase());
    const externalRequestExamples = [
        {
            exchange_id: "example-dna",
            request_type: "DNA Analysis",
            to_agency: "DPS Crime Lab",
            status: "in_progress",
            assigned_to: "Lab Liaison",
            submitted_at: new Date().toISOString(),
            requested_by: "Det. Smith",
            legal_authority: "Lab Submission",
            requested_records: "Biological material comparison and DNA report.",
            summary: "DNA comparison submitted to DPS Crime Lab.",
            audit_log: "Example workflow: submitted, received, in analysis.",
        },
        {
            exchange_id: "example-namus",
            request_type: "NamUs Entry",
            to_agency: "NamUs",
            status: "submitted",
            assigned_to: "Case Detective",
            submitted_at: new Date().toISOString(),
            requested_by: "Investigator",
            legal_authority: "Missing persons coordination",
            requested_records: "Case profile and missing person details.",
            summary: "NamUs entry submitted for national visibility.",
            audit_log: "Example workflow: created and submitted.",
        },
        {
            exchange_id: "example-morgue",
            request_type: "Morgue Comparison",
            to_agency: "Dallas ME",
            status: "pending",
            assigned_to: "Decedent ID Coordinator",
            submitted_at: new Date().toISOString(),
            requested_by: "Supervisor",
            legal_authority: "Inter-agency request",
            requested_records: "Decedent comparison, fingerprints, dental, and DNA status.",
            summary: "Medical examiner comparison pending.",
            audit_log: "Example workflow: requested, pending review.",
        },
        {
            exchange_id: "example-hospital",
            request_type: "Hospital Inquiry",
            to_agency: "Regional Network",
            status: "completed",
            assigned_to: "Analyst",
            submitted_at: new Date().toISOString(),
            requested_by: "Investigator",
            legal_authority: "Court-authorized request",
            requested_records: "Admission or encounter confirmation.",
            summary: "Regional hospital inquiry completed.",
            audit_log: "Example workflow: submitted, reviewed, completed.",
        },
        {
            exchange_id: "example-fingerprint",
            request_type: "Fingerprint Comparison",
            to_agency: "DPS",
            status: "match_found",
            assigned_to: "Evidence Technician",
            submitted_at: new Date().toISOString(),
            requested_by: "Investigator",
            legal_authority: "Evidence Transfer",
            requested_records: "Latent print comparison and response report.",
            summary: "Fingerprint comparison returned a possible match.",
            audit_log: "Example workflow: submitted, analysis complete, match found.",
        },
    ];
    const externalRequests = agencyExchanges.length > 0 ? agencyExchanges : externalRequestExamples;
    const selectedRequestDetails = selectedExternalRequest || externalRequests[0];

    return (
        <div className="case-detail-page">
            <Link className="case-back-link" to="/cases">Back to Cases</Link>

            <div className="case-section">
                <div className="case-card-header">
                    <div>
                        <h1 className="case-title">Case #{caseItem.case_number}</h1>
                        <p>{personName}</p>
                    </div>

                    <button
                        className="case-action-button"
                        onClick={() => setShowSightingForm(!showSightingForm)}
                    >
                        {showSightingForm ? "Close Sighting" : "Add Sighting"}
                    </button>
                </div>

                <div className="case-card-header case-status-row">
                    <span className={`priority-badge priority-${caseItem.priority_level}`}>
                        {caseItem.priority_level}
                    </span>
                    <span className="status-badge">Status: {caseItem.case_status}</span>
                    <span className="status-badge">Agency ID: {caseItem.agency_id}</span>
                    <span className="status-badge">
                        Investigator ID: {caseItem.investigator_id}
                    </span>
                </div>

                {showSightingForm && (
                    <form className="case-sighting-form" onSubmit={submitSighting}>
                        <input
                            name="location"
                            placeholder="Location"
                            value={sightingForm.location}
                            onChange={handleSightingChange}
                        />

                        <input
                            name="latitude"
                            placeholder="Latitude"
                            value={sightingForm.latitude}
                            onChange={handleSightingChange}
                        />

                        <input
                            name="longitude"
                            placeholder="Longitude"
                            value={sightingForm.longitude}
                            onChange={handleSightingChange}
                        />

                        <input
                            name="confidence_score"
                            placeholder="Confidence Score 0-1"
                            value={sightingForm.confidence_score}
                            onChange={handleSightingChange}
                        />

                        <textarea
                            name="description"
                            placeholder="Description"
                            value={sightingForm.description}
                            onChange={handleSightingChange}
                        />

                        <button type="submit">Add Sighting</button>
                    </form>
                )}

                {sightingMessage && <p>{sightingMessage}</p>}
            </div>

            <div className="case-tabs" role="tablist" aria-label="Case information tabs">
                {caseTabs.map(([tabId, label]) => (
                    <button
                        key={tabId}
                        type="button"
                        className={activeTab === tabId ? "active" : ""}
                        onClick={() => setActiveTab(tabId)}
                    >
                        {label}
                    </button>
                ))}
            </div>

            {activeTab === "overview" && person && (
                <div className="case-section missing-person-profile case-tab-panel">
                    <div className="missing-person-photo">
                        {person.photo_url ? (
                            <img
                                src={person.photo_url}
                                alt={`${person.first_name} ${person.last_name}`}
                            />
                        ) : (
                            <div className="missing-person-photo-placeholder">
                                <span>No Photo</span>
                            </div>
                        )}
                    </div>

                    <div className="missing-person-details case-overview-grid">
                        <h2>Subject Profile</h2>
                        <p>Name: {personName}</p>
                        <p>Age: {person.age}</p>
                        <p>Eye Color: {person.eye_color}</p>
                        <p>Hair Color: {person.hair_color}</p>
                        <p>Height: {person.height}</p>
                        <p>Weight: {person.weight}</p>
                        <p>Risk Level: {person.risk_level}</p>
                        <p>Assigned Investigator: {caseItem.investigator_id}</p>
                        <p>Reporting Agency: {caseItem.agency_id}</p>
                        <p>Last Seen: {person.last_seen_location}</p>
                        <p>Description: {person.description}</p>
                    </div>
                </div>
            )}

            {activeTab === "timeline" && (
                <div className="case-section case-tab-panel">
                    <h2>Timeline</h2>
                    <div className="case-timeline-list">
                        {timelineEvents.map((event) => (
                            <article key={event.event_id} className="timeline-card">
                                <strong>{event.timestamp || "Timeline event"}</strong>
                                <p>{event.event_type}: {event.description}</p>
                                <small>{event.location}</small>
                            </article>
                        ))}

                        {sortedSightings.map((sighting, index) => (
                            <article key={sighting.sighting_id} className="timeline-card">
                                <strong>{sighting.sighting_time || sighting.created_at || `Sighting ${index + 1}`}</strong>
                                <p>Sighting reported at {sighting.location}</p>
                                <small>{sighting.description}</small>
                            </article>
                        ))}
                    </div>
                </div>
            )}

            {activeTab === "escapeRoutes" && (
                <div className="case-section case-tab-panel">
                    <EscapeRouteAnalysis
                        embedded
                        caseContext={{
                            caseNumber: caseItem.case_number || `Case ${caseItem.case_id}`,
                            lastSeenLocation: person?.last_seen_location || "",
                            sightings: sortedSightings,
                            associateLocations,
                        }}
                    />
                </div>
            )}

            {activeTab === "sightings" && (
                <div className="case-section case-tab-panel">
                    <h2>Case Geography</h2>
                    <SightingMap
                        sightings={sortedSightings}
                        associateLocations={associateLocations}
                    />
                </div>
            )}

            {activeTab === "evidence" && (
                <div className="case-section case-tab-panel">
                    <h2>Evidence</h2>
                    {evidence.length === 0 ? (
                        <p>No evidence uploaded.</p>
                    ) : (
                        evidence.map((item) => (
                            <article key={item.evidence_id} className="queue-item">
                                <div>
                                    <strong>{item.evidence_type}</strong>
                                    <span>{item.is_sensitive ? "Sensitive" : "Standard"}</span>
                                </div>
                                <p>{item.description}</p>
                                <p>File: {item.file_name}</p>
                                <div className="case-action-row">
                                    <button onClick={() => viewEvidence(item.evidence_id)}>
                                        Open Evidence
                                    </button>
                                    <button onClick={() => loadEvidenceChain(item.evidence_id)}>
                                        View Chain of Custody
                                    </button>
                                    <button
                                        onClick={() =>
                                            markEvidenceSensitive(item.evidence_id, !item.is_sensitive)
                                        }
                                    >
                                        {item.is_sensitive ? "Unmark Sensitive" : "Mark Sensitive"}
                                    </button>
                                </div>

                                {evidenceChains[item.evidence_id]?.map((event) => (
                                    <div key={event.chain_id} className="custody-event-card">
                                        <p><strong>Action:</strong> {event.action}</p>
                                        <p><strong>Details:</strong> {event.details}</p>
                                        <p><strong>Date:</strong> {event.created_at}</p>
                                    </div>
                                ))}
                            </article>
                        ))
                    )}
                </div>
            )}

            {activeTab === "associates" && (
                <div className="case-section case-tab-panel">
                    <div className="case-associates-layout">
                        <section>
                            <h2>Known Associates</h2>
                            {associates.length === 0 ? (
                                <p>No known associates recorded.</p>
                            ) : (
                                <div className="case-associate-list">
                                    {associates.map((associate) => (
                                        <article key={associate.id} className="case-associate-card">
                                            <strong>{associate.name}</strong>
                                            <span>{associate.relationship}</span>
                                            <p>{associate.address}</p>
                                            {associate.latitude && associate.longitude ? (
                                                <small>Mapped at {associate.latitude}, {associate.longitude}</small>
                                            ) : (
                                                <small>No map coordinates recorded.</small>
                                            )}
                                            {associate.notes && <p>{associate.notes}</p>}
                                        </article>
                                    ))}
                                </div>
                            )}
                        </section>

                        <form className="case-associate-form" onSubmit={submitAssociate}>
                            <h2>Add Associate</h2>
                            <input
                                name="name"
                                value={associateForm.name}
                                onChange={handleAssociateChange}
                                placeholder="Associate name"
                            />
                            <input
                                name="relationship"
                                value={associateForm.relationship}
                                onChange={handleAssociateChange}
                                placeholder="Relationship"
                            />
                            <input
                                name="address"
                                value={associateForm.address}
                                onChange={handleAssociateChange}
                                placeholder="Address or known location"
                            />
                            <div className="case-associate-coordinate-row">
                                <input
                                    name="latitude"
                                    value={associateForm.latitude}
                                    onChange={handleAssociateChange}
                                    placeholder="Latitude"
                                />
                                <input
                                    name="longitude"
                                    value={associateForm.longitude}
                                    onChange={handleAssociateChange}
                                    placeholder="Longitude"
                                />
                            </div>
                            <textarea
                                name="notes"
                                value={associateForm.notes}
                                onChange={handleAssociateChange}
                                placeholder="Notes, caution flags, or investigative context"
                            />
                            <button type="submit">Add Associate</button>
                            {associateMessage && <p>{associateMessage}</p>}
                        </form>
                    </div>
                </div>
            )}

            {activeTab === "leads" && (
                <div className="case-section case-tab-panel">
                    <h2>Leads</h2>
                    <div className="beacon-status-list">
                        <span>New leads: {externalRecords.length}</span>
                        <span>Assigned leads: {agencyExchanges.length}</span>
                        <span>Pending follow-ups: {sortedSightings.length}</span>
                        <span>Closed leads: 0</span>
                    </div>
                </div>
            )}

            {activeTab === "intelligence" && (
                <div className="case-section case-tab-panel">
                    <h2>Intelligence</h2>
                    <div className="case-intelligence-grid">
                        {intelligenceProfileItems.map(([title, detail]) => (
                            <article key={title} className="case-intelligence-card">
                                <strong>{title}</strong>
                                <p>{detail}</p>
                            </article>
                        ))}
                    </div>

                    <h3>Authorized External Records</h3>
                    {externalRecords.length === 0 ? (
                        <p>No external records found for this person.</p>
                    ) : (
                        <div className="external-record-links">
                            {externalRecords.map((record) => (
                                <button
                                    key={record.id}
                                    type="button"
                                    onClick={() => setSelectedExternalRecord(record)}
                                >
                                    {getExternalRecordName(record)}
                                </button>
                            ))}
                        </div>
                    )}

                    {selectedExternalRecord && (
                        <div className="external-record-detail">
                            <div className="case-card-header">
                                <h3>{getExternalRecordName(selectedExternalRecord)}</h3>
                                <button
                                    type="button"
                                    onClick={() => setSelectedExternalRecord(null)}
                                >
                                    Close
                                </button>
                            </div>
                            <p>
                                Name: {selectedExternalRecord.first_name}{" "}
                                {selectedExternalRecord.last_name}
                            </p>
                            <p>Age: {selectedExternalRecord.age || "Not provided"}</p>
                            <p>Location: {selectedExternalRecord.location || "Not provided"}</p>
                            <p>Notes: {selectedExternalRecord.notes || "Not provided"}</p>
                        </div>
                    )}
                </div>
            )}

            {activeTab === "externalRequests" && (
                <div className="case-section case-tab-panel">
                    <h2>External Requests & Collaboration</h2>
                    <div className="case-external-request-layout">
                        <section className="case-external-request-list">
                            <div className="external-request-table-head">
                                <span>Request Type</span>
                                <span>Agency</span>
                                <span>Status</span>
                            </div>

                            {externalRequests.map((request) => (
                                <button
                                    key={request.exchange_id}
                                    type="button"
                                    className={`external-request-row ${selectedRequestDetails?.exchange_id === request.exchange_id ? "active" : ""}`}
                                    onClick={() => setSelectedExternalRequest(request)}
                                >
                                    <span>{request.request_type || request.information_type}</span>
                                    <span>{request.to_agency}</span>
                                    <span>{statusLabel(request.status)}</span>
                                </button>
                            ))}
                        </section>

                        <section className="case-external-request-detail">
                            <div className="audit-panel-heading">
                                <span>Request Detail</span>
                                <strong>{selectedRequestDetails?.request_type || selectedRequestDetails?.information_type}</strong>
                            </div>
                            <dl className="external-request-detail-grid">
                                <div>
                                    <dt>Submission Date</dt>
                                    <dd>
                                        {selectedRequestDetails?.submitted_at || selectedRequestDetails?.created_at
                                            ? new Date(selectedRequestDetails.submitted_at || selectedRequestDetails.created_at).toLocaleString()
                                            : "Not submitted"}
                                    </dd>
                                </div>
                                <div>
                                    <dt>Requestor</dt>
                                    <dd>{selectedRequestDetails?.requesting_officer || selectedRequestDetails?.requested_by || `User ${selectedRequestDetails?.approved_by || "Unknown"}`}</dd>
                                </div>
                                <div>
                                    <dt>Authority</dt>
                                    <dd>{selectedRequestDetails?.legal_authority || "Not recorded"}</dd>
                                </div>
                                <div>
                                    <dt>Follow-Up Reminder</dt>
                                    <dd>{selectedRequestDetails?.due_date ? new Date(selectedRequestDetails.due_date).toLocaleString() : "No reminder set"}</dd>
                                </div>
                                <div>
                                    <dt>Documents</dt>
                                    <dd>{selectedRequestDetails?.attachments || selectedRequestDetails?.requested_records || "No documents linked"}</dd>
                                </div>
                                <div>
                                    <dt>Responses</dt>
                                    <dd>{selectedRequestDetails?.summary || "No response recorded yet"}</dd>
                                </div>
                            </dl>
                            <div className="external-request-audit">
                                <strong>Audit History</strong>
                                <p>{selectedRequestDetails?.audit_log || "Created in Beacon; future views, responses, uploads, and status changes will be logged."}</p>
                            </div>
                        </section>
                    </div>
                </div>
            )}

            {activeTab === "documents" && (
                <div className="case-section case-tab-panel">
                    <h2>Documents</h2>
                    <div className="beacon-status-list">
                        <span>Reports pending: 0</span>
                        <span>Legal documents: 0</span>
                        <span>Evidence files: {evidence.length}</span>
                    </div>
                </div>
            )}

            {activeTab === "audit" && (
                <div className="case-section case-tab-panel">
                    <h2>Audit Log</h2>
                    {agencyExchanges.length === 0 ? (
                        <p>No agency exchanges recorded for this case.</p>
                    ) : (
                        <div className="case-agency-exchanges">
                            {agencyExchanges.map((exchange) => (
                                <article key={exchange.exchange_id} className="agency-exchange-card">
                                    <div>
                                        <strong>{exchange.from_agency} to {exchange.to_agency}</strong>
                                        <span>{exchange.information_type}</span>
                                    </div>
                                    <p>{exchange.summary}</p>
                                    <small>
                                        Approved by user {exchange.approved_by} | {exchange.status}
                                    </small>
                                </article>
                            ))}
                        </div>
                    )}
                </div>
            )}

        </div>
    );
}

export default CaseDetail;
