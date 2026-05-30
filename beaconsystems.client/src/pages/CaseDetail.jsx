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
                ]);

                const [
                    sightingsData,
                    timelineData,
                    evidenceData,
                    personData,
                    externalRecordsData,
                ] = await Promise.all([
                    sightingsResponse.ok ? sightingsResponse.json() : [],
                    timelineResponse.ok ? timelineResponse.json() : [],
                    evidenceResponse.ok ? evidenceResponse.json() : [],
                    personResponse.ok ? personResponse.json() : null,
                    externalRecordsResponse.ok ? externalRecordsResponse.json() : [],
                ]);

                if (!isMounted) return;

                setSightings(Array.isArray(sightingsData) ? sightingsData : []);
                setTimelineEvents(Array.isArray(timelineData) ? timelineData : []);
                setEvidence(Array.isArray(evidenceData) ? evidenceData : []);
                setPerson(personData);
                setExternalRecords(
                    Array.isArray(externalRecordsData) ? externalRecordsData : []
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

    return (
        <div className="case-detail-page">
            <Link className="case-back-link" to="/cases">Back to Cases</Link>

            <div className="case-section">
                <div className="case-card-header">
                    <div>
                        <h1 className="case-title">Case {caseItem.case_number}</h1>
                        <p>Investigative case workspace</p>
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

            {person && (
                <div className="case-section">
                    <h2>Missing Person Profile</h2>
                    <p>Name: {person.first_name} {person.last_name}</p>
                    <p>Age: {person.age}</p>
                    <p>Eye Color: {person.eye_color}</p>
                    <p>Hair Color: {person.hair_color}</p>
                    <p>Height: {person.height}</p>
                    <p>Weight: {person.weight}</p>
                    <p>Risk Level: {person.risk_level}</p>
                    <p>Status: {person.status}</p>
                    <p>Last Seen: {person.last_seen_location}</p>
                    <p>Description: {person.description}</p>
                </div>
            )}

            <hr />

            <h2>Linked External Records</h2>
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
                <div className="case-section external-record-detail">
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

            <hr />

            <h2>Evidence</h2>
            {evidence.length === 0 ? (
                <p>No evidence uploaded.</p>
            ) : (
                evidence.map((item) => (
                    <div key={item.evidence_id} className="case-section">
                        <p><strong>Type:</strong> {item.evidence_type}</p>
                        {item.is_sensitive && <p><strong>SENSITIVE EVIDENCE</strong></p>}
                        <p><strong>Description:</strong> {item.description}</p>
                        <p><strong>File:</strong> {item.file_name}</p>

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

                        {evidenceChains[item.evidence_id]?.map((event) => (
                            <div key={event.chain_id} style={styles.chainCard}>
                                <p><strong>Action:</strong> {event.action}</p>
                                <p><strong>Details:</strong> {event.details}</p>
                                <p><strong>Date:</strong> {event.created_at}</p>
                            </div>
                        ))}
                    </div>
                ))
            )}

            <hr />

            <h2>Case Timeline</h2>
            <div className="case-section">
                {timelineEvents.map((event) => (
                    <div key={event.event_id} style={styles.card}>
                        <strong>{event.event_type}</strong>
                        <p>{event.description}</p>
                        <p>Location: {event.location}</p>
                        <p>{event.timestamp}</p>
                    </div>
                ))}

                {sortedSightings.map((sighting, index) => (
                    <div key={sighting.sighting_id} className="timeline-card">
                        <strong>Sighting #{index + 1} Reported</strong>
                        <p>Location: {sighting.location}</p>
                        <p>Description: {sighting.description}</p>
                        <p>Confidence: {sighting.confidence_score ?? "Unknown"}</p>
                        <p>Coordinates: {sighting.latitude}, {sighting.longitude}</p>
                        <p>
                            Time: {sighting.sighting_time || sighting.created_at || "Unknown"}
                        </p>
                    </div>
                ))}
            </div>

            <hr />

            <h2>Sighting Map</h2>
            <SightingMap sightings={sortedSightings} />

        </div>
    );
}
const styles = {
    card: {
        border: "1px solid gray",
        padding: "12px",
        margin: "10px 0",
        borderRadius: "8px",
    },

    chainCard: {
        border: "1px solid lightgray",
        padding: "8px",
        marginTop: "8px",
        borderRadius: "6px",
        backgroundColor: "#f7f7f7",
    },

    evidenceActions: {
        display: "flex",
        gap: "10px",
        flexWrap: "wrap",
        marginTop: "12px",
        marginBottom: "12px",
    },
};

export default CaseDetail;
