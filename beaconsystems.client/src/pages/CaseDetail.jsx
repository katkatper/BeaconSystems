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
    const [investigators, setInvestigators] = useState([]);
    const [selectedInvestigator, setSelectedInvestigator] = useState("");
    const [assignmentMessage, setAssignmentMessage] = useState("");
    const [evidence, setEvidence] = useState([]);
    const [evidenceChains, setEvidenceChains] = useState({});

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
                    usersResponse,
                    evidenceResponse,
                    personResponse,
                    externalRecordsResponse,
                ] = await Promise.all([
                    fetch(`http://127.0.0.1:8000/sightings/?case_id=${id}`, {
                        headers: authHeaders,
                    }),
                    fetch(`http://127.0.0.1:8000/timeline-events/?case_id=${id}`),
                    fetch("http://127.0.0.1:8000/admin/users/", {
                        headers: authHeaders,
                    }),
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
                    usersData,
                    evidenceData,
                    personData,
                    externalRecordsData,
                ] = await Promise.all([
                    sightingsResponse.ok ? sightingsResponse.json() : [],
                    timelineResponse.ok ? timelineResponse.json() : [],
                    usersResponse.ok ? usersResponse.json() : [],
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

                const usersArray = Array.isArray(usersData) ? usersData : [];
                setInvestigators(
                    usersArray.filter(
                        (user) => user.role === "investigator" || user.role === "admin"
                    )
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

    const assignInvestigator = async () => {
        const token = localStorage.getItem("token");

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/cases/${id}/assign-investigator?investigator_id=${selectedInvestigator}`,
                {
                    method: "PUT",
                    headers: { Authorization: `Bearer ${token}` },
                }
            );

            if (!response.ok) throw new Error("Failed to assign investigator");

            const data = await response.json();
            setAssignmentMessage(data.message);
            setCaseItem({
                ...caseItem,
                investigator_id: selectedInvestigator,
            });
        } catch (err) {
            console.error(err);
            setAssignmentMessage("Could not assign investigator.");
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

    return (
        <div className="case-detail-page">
            <Link to="/">Back to Dashboard</Link>

            <div className="case-section">
                <h1 className="case-title">Case {caseItem.case_number}</h1>
                <p>Investigative case workspace and operational intelligence view</p>

                <div className="case-card-header">
                    <span className={`priority-badge priority-${caseItem.priority_level}`}>
                        {caseItem.priority_level}
                    </span>
                    <span className="status-badge">{caseItem.case_status}</span>
                </div>
            </div>

            <p>Status: {caseItem.case_status}</p>
            <p>Priority: {caseItem.priority_level}</p>
            <p>Last Seen: {caseItem.last_seen_location}</p>
            <p>Notes: {caseItem.notes}</p>
            <p>Agency ID: {caseItem.agency_id}</p>
            <p>Investigator ID: {caseItem.investigator_id}</p>

            <div className="case-section">
                <h2>Investigator Assignment</h2>

                <select
                    value={selectedInvestigator}
                    onChange={(e) => setSelectedInvestigator(e.target.value)}
                >
                    <option value="">Select Investigator</option>
                    {investigators.map((user) => (
                        <option key={user.user_id} value={user.user_id}>
                            {user.username} - {user.role}
                        </option>
                    ))}
                </select>

                <button onClick={assignInvestigator}>Assign</button>
                {assignmentMessage && <p>{assignmentMessage}</p>}
            </div>

            {person && (
                <div className="case-section">
                    <h2>Missing Person Intelligence Profile</h2>
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
                externalRecords.map((record) => (
                    <div key={record.id} style={styles.card}>
                        <strong>{record.record_type}</strong>
                        <p>Name: {record.first_name} {record.last_name}</p>
                        <p>Age: {record.age}</p>
                        <p>Location: {record.location}</p>
                        <p>Notes: {record.notes}</p>
                    </div>
                ))
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
                        <button onClick={() => markEvidenceSensitive(item.evidence_id, true)}>
                            Mark Sensitive
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

            <hr />

            <h2>Add Sighting</h2>
            <form onSubmit={submitSighting}>
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

                <textarea
                    name="description"
                    placeholder="Description"
                    value={sightingForm.description}
                    onChange={handleSightingChange}
                />

                <input
                    name="confidence_score"
                    placeholder="Confidence Score 0-1"
                    value={sightingForm.confidence_score}
                    onChange={handleSightingChange}
                />

                <button type="submit">Add Sighting</button>
            </form>

            {sightingMessage && <p>{sightingMessage}</p>}
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
};

export default CaseDetail;
