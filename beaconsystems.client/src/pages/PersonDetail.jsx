import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

const formatDate = (value) => {
    if (!value) {
        return "Not recorded";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "Not recorded";
    }

    return date.toLocaleDateString();
};

function SubjectProfile({ person }) {
    const sections = [
        ["Demographics", `Age ${person.age || "unknown"} | ${person.eye_color || "unknown"} eyes | ${person.hair_color || "unknown"} hair`],
        ["Criminal History", person.criminal_history || "No criminal history notes recorded."],
        ["Warrants", person.warrants || "No warrant notes recorded."],
        ["Arrests", person.arrests || "No arrest notes recorded."],
        ["Charges", person.charges || "No charge notes recorded."],
        ["Convictions", person.convictions || "No conviction notes recorded."],
        ["Corrections History", person.corrections_history || "No corrections history recorded."],
        ["Known Associates", person.known_associates || "No known associates recorded."],
        ["Intelligence Notes", person.intelligence_notes || "No intelligence notes recorded."],
    ];

    return (
        <section className="person-profile-card subject-profile-card">
            <div className="subject-profile-header">
                <span>Subject Profile</span>
                <h2>Criminal History Summary</h2>
            </div>

            <div className="criminal-summary-grid">
                <div><span>Arrests</span><strong>{person.criminal_arrests_count || 0}</strong></div>
                <div><span>Felony Convictions</span><strong>{person.felony_convictions_count || 0}</strong></div>
                <div><span>Active Warrants</span><strong>{person.active_warrants_count || 0}</strong></div>
                <div><span>Protective Orders</span><strong>{person.protective_orders_count || 0}</strong></div>
                <div><span>Last Arrest</span><strong>{formatDate(person.last_arrest_date)}</strong></div>
                <div><span>Most Serious Offense</span><strong>{person.most_serious_offense || "Not recorded"}</strong></div>
            </div>

            <div className="subject-profile-section-grid">
                {sections.map(([title, detail]) => (
                    <article key={title}>
                        <strong>{title}</strong>
                        <p>{detail}</p>
                    </article>
                ))}
            </div>
        </section>
    );
}


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

                <SubjectProfile person={person} />
            </div>
        </div>
    );
}

export default PersonDetail;
