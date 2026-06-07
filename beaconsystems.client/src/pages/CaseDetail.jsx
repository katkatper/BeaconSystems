import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import SightingMap from "./SightingMap.jsx";

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
    const [activeTab, setActiveTab] = useState("overview");

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
    const personName = person
        ? `${person.first_name || ""} ${person.last_name || ""}`.trim()
        : "Missing Person";
    const caseTabs = [
        ["overview", "Overview"],
        ["timeline", "Timeline"],
        ["sightings", "Sightings"],
        ["evidence", "Evidence"],
        ["leads", "Leads"],
        ["intelligence", "Intelligence"],
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

            {activeTab === "sightings" && (
                <div className="case-section case-tab-panel">
                    <h2>Sightings</h2>
                    <SightingMap sightings={sortedSightings} />
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
