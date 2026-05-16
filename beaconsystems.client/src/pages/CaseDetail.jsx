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
    const [Timeline_Events, setTimeline_Events] = useState([]);


    const [sightingForm, setSightingForm] = useState({
        location: "",
        latitude: "",
        longitude: "",
        description: "",
        confidence_score: "",
    });

    useEffect(() => {
        const token = localStorage.getItem("token");

        fetch(`http://127.0.0.1:8000/cases/${id}`, {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        })
            .then((res) => {
                if (!res.ok) {
                    throw new Error("Failed to load case");
                }
                return res.json();
            })
            .then((data) => {
                setCaseItem(data);

                fetch(
                    `http://127.0.0.1:8000/external-records/?person_id=${data.person_id}`,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                )
                    .then((res) => res.json())
                    .then((externalData) => {
                        setExternalRecords(externalData);
                    })
                    .catch((err) => console.error(err));

                return fetch(
                    `http://127.0.0.1:8000/persons/${data.person_id}`,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );
            })
            .then((res) => res.json())
            .then((personData) => {
                setPerson(personData);
            })
            .catch((err) => {
                console.error(err);
                setError("Could not load case details.");
            });

        fetch(`http://127.0.0.1:8000/sightings/?case_id=${id}`, {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        })
            .then((res) => {
                if (!res.ok) {
                    throw new Error("Failed to load sightings");
                }
                return res.json();
            })
            .then((data) => {
                setSightings(data);
            })
            .catch((err) => {
                console.error(err);
            });

        fetch(`http://127.0.0.1:8000/timeline-events/?case_id=${id}`)
            .then((res) => res.json())
            .then((data) => {
                setTimeline_Events(data);
            })
            .catch((err) => {
                console.error(err);
            });

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
                latitude: sightingForm.latitude
                    ? Number(sightingForm.latitude)
                    : null,
                longitude: sightingForm.longitude
                    ? Number(sightingForm.longitude)
                    : null,
                description: sightingForm.description,
                confidence_score: sightingForm.confidence_score
                    ? Number(sightingForm.confidence_score)
                    : null,
                image_url: null,
            };

            const response = await fetch(
                "http://127.0.0.1:8000/sightings/",
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
                throw new Error("Failed to add sighting");
            }

            const data = await response.json();

            const newSighting = {
                sighting_id: data.sighting_id,
                ...payload,
                created_at: new Date().toISOString(),
            };

            setSightings([...sightings, newSighting]);

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

    if (error) {
        return <p>{error}</p>;
    }

    if (!caseItem) {
        return <p>Loading case details...</p>;
    }

    const sortedSightings = [...sightings].sort(
        (a, b) =>
            new Date(a.sighting_time || a.created_at) -
            new Date(b.sighting_time || b.created_at)
    );

    return (
        <div>
            <Link to="/">Back to Dashboard</Link>

            <h1>Case Detail</h1>

            <h2>{caseItem.case_number}</h2>

            <p>Status: {caseItem.case_status}</p>
            <p>Priority: {caseItem.priority_level}</p>
            <p>Last Seen: {caseItem.last_seen_location}</p>
            <p>Notes: {caseItem.notes}</p>
            <p>Investigator ID: {caseItem.investigator_id}</p>
            <p>Agency ID: {caseItem?.agency_id}</p>

            {person && (
                <div
                    style={{
                        border: "1px solid gray",
                        padding: "15px",
                        margin: "15px 0",
                        borderRadius: "8px",
                    }}
                >
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
                externalRecords.map((record) => (
                    <div
                        key={record.id}
                        style={{
                            border: "1px solid gray",
                            margin: "10px",
                            padding: "12px",
                            borderRadius: "8px",
                        }}
                    >
                        <strong>{record.record_type}</strong>
                        <p>Name: {record.first_name} {record.last_name}</p>
                        <p>Age: {record.age}</p>
                        <p>Location: {record.location}</p>
                        <p>Notes: {record.notes}</p>
                    </div>
                ))
            )}

            <hr />

            <h2>Case Timeline</h2>

            <div
                style={{
                    border: "1px solid gray",
                    margin: "10px",
                    padding: "12px",
                    borderRadius: "8px",
                }}
            >
                {Timeline_Events.map((event) => (
                    <div
                        key={event.event_id}
                        style={{
                            border: "1px solid gray",
                            margin: "10px",
                            padding: "12px",
                            borderRadius: "8px",
                        }}
                    >
                        <strong>{event.event_type}</strong>

                        <p>{event.description}</p>

                        <p>Location: {event.location}</p>

                        <p>{event.timestamp}</p>
                    </div>
               
                ))}

                {sortedSightings.map((sighting, index) => (
                    <div
                    key={sighting.sighting_id}
                    style={{
                        border: "1px solid gray",
                        margin: "10px",
                        padding: "12px",
                        borderRadius: "8px",
                    }}
                >
                    <strong>Sighting #{index + 1} Reported</strong>
                    <p>Location: {sighting.location}</p>
                    <p>Description: {sighting.description}</p>
                    <p>Confidence: {sighting.confidence_score ?? "Unknown"}</p>
                    <p>Coordinates: {sighting.latitude}, {sighting.longitude}</p>
                    <p>
                        Time:{" "}
                        {sighting.sighting_time ||
                            sighting.created_at ||
                            "Unknown"}
                    </p>
                </div>
            ))}

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
    </div>
)};

export default CaseDetail;