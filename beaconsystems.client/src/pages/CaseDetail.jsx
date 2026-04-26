import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";



//CASE DETAIL PAGE

function CaseDetail() {

    const { id } = useParams();

    const [caseItem, setCaseItem] = useState(null);

    const [sightings, setSightings] = useState([]);

    const [error, setError] = useState("");

    const [sightingMessage, setSightingMessage] = useState("");

    const [sightingForm, setSightingForm] = useState({

        location: "",

        latitude: "",

        longitude: "",

        description: "",

        confidence_score: "",

    });

    //FETCH CASE DETAILS AND SIGHTINGS ON COMPONENT LOAD

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

    }, [id]);

    //HANDLE SIGHTING FORM INPUT CHANGES

    const handleSightingChange = (e) => {

        setSightingForm({

            ...sightingForm,

            [e.target.name]: e.target.value,

        });
    };

    //SUBMIT NEW SIGHTING TO BACKEND

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

            //BASIC VALIDATION

            const response = await fetch("http://127.0.0.1:8000/sightings/", {

                method: "POST",

                headers: {

                    "Content-Type": "application/json",

                    Authorization: `Bearer ${token}`,
                },

                body: JSON.stringify(payload),
            });

            if (!response.ok) {

                throw new Error("Failed to add sighting");
            }

            //GET NEWLY CREATED SIGHTING ID FROM RESPONSE


            const data = await response.json();

            setSightingMessage("Sighting added successfully.");

            setSightings([

                ...sightings,
                {
                    sighting_id: data.sighting_id,

                    ...payload,
                },
            ]);

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

    //RENDER CASE DETAILS AND SIGHTINGS

    if (error) {

        return <p>{error}</p>;
    }

    if (!caseItem) {

        return <p>Loading case details...</p>;
    }
    

    return (

        <div>
            <Link to="/">Back to Dashboard</Link>

            <h1>Case Detail</h1>

            <h2>{caseItem.case_number}</h2>

            <p>Status: {caseItem.case_status}</p>

            <p>Priority: {caseItem.priority_level}</p>

            <p>Last Seen: {caseItem.last_seen_location}</p>

            <p>Notes: {caseItem.notes}</p>

            <p>Person ID: {caseItem.person_id}</p>

            <p>Investigator ID: {caseItem.investigator_id}</p>

            <p>Agency ID: {caseItem.reporting_agency_id}</p>

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
                <strong>Case Opened</strong>

                <p>Investigation initiated</p>

            </div>


            <div
                style={{

                    border: "1px solid gray",

                    margin: "10px",

                    padding: "12px",

                    borderRadius: "8px",
                }}
            >
                <strong>Last Seen</strong>

                <p>{caseItem.last_seen_location}</p>

            </div>

            {sightings.map((sighting) => (

                <div

                    key={sighting.sighting_id}

                    style={{

                        border: "1px solid gray",

                        margin: "10px",

                        padding: "12px",

                        borderRadius: "8px",
                    }}
                >
                    <strong>Sighting Reported</strong>

                    <p>Location: {sighting.location}</p>

                    <p>Description: {sighting.description}</p>

                    <p>Confidence: {sighting.confidence_score}</p>

                    <p>
                        Coordinates: {sighting.latitude}, {sighting.longitude}
                    </p>

                </div>
            ))}

        // FORM TO ADD NEW SIGHTING

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

export default CaseDetail;