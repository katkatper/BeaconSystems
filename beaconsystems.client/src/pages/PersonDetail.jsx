import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";


function PersonDetail() {

    const { id } = useParams();
    const [person, setPerson] = useState(null);
    const [cases, setCases] = useState([]);

    useEffect(() => {
        const token = localStorage.getItem("token");

        fetch(`http://127.0.0.1:8000/persons/${id}`, {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        })
            .then(res => res.json())
            .then(data => {
                setPerson(data);

                return fetch(
                    `http://127.0.0.1:8000/cases/by-person/${id}`,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );
            })
            .then(res => res.json())
            .then(caseData => {
                setCases(caseData);
            });
    }, [id]);

    if (!person) {
        return (
            <div className="person-detail-page">
                <p>Loading person profile...</p>
            </div>
        );
    }

    return (

        <div className="person-detail-page">
            <header className="person-detail-header">
                <h1>{person.first_name} {person.last_name}</h1>
            </header>

            <div className="person-detail-grid">
                <section className="person-profile-card person-profile-overview">
                    <div className="person-profile-photo">
                        {person.photo_url ? (
                            <img
                                src={person.photo_url}
                                alt={`${person.first_name} ${person.last_name}`}
                            />
                        ) : (
                            <span>No Photo</span>
                        )}
                    </div>

                    <div className="person-profile-details">
                        <h2>Profile</h2>
                        <p>Age: {person.age || "Unknown"}</p>
                        <p>Eye Color: {person.eye_color || "Not recorded"}</p>
                        <p>Hair Color: {person.hair_color || "Not recorded"}</p>
                        <p>Height: {person.height || "Not recorded"}</p>
                        <p>Weight: {person.weight || "Not recorded"}</p>
                        <p>Risk Level: {person.risk_level || "Unknown"}</p>
                        <p>Status: {person.status || "Unknown"}</p>
                        <p>Last Seen: {person.last_seen_location || "Not recorded"}</p>
                        <p>{person.description || "No description recorded."}</p>
                    </div>
                </section>

                <section className="person-profile-card">
                    <h2>Related Cases</h2>

                    {cases.length === 0 && <p>No cases found.</p>}

                    {[...cases]
                        .sort((firstCase, secondCase) =>
                            (firstCase.case_number || "").localeCompare(secondCase.case_number || "")
                        )
                        .slice(0, 6)
                        .map((c) => (
                            <article key={c.case_id} className="queue-item">
                                <p>Case #: {c.case_number}</p>
                                <p>Status: {c.case_status}</p>

                                <button
                                    type="button"
                                    onClick={() => {
                                        window.location.href = `/cases/${c.case_id}`;
                                    }}
                                >
                                    Open Case
                                </button>
                            </article>
                        ))}
                </section>
            </div>
        </div>
    );
}

export default PersonDetail;
