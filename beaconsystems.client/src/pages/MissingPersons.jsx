import React, { useEffect, useState } from "react";

function MissingPersonsList() {

    const [persons, setPersons] = useState([]);
    const [error, setError] = useState("");
    const [showMorePersons, setShowMorePersons] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem("token");


        fetch("http://127.0.0.1:8000/persons/", {

            headers: {
                Authorization: `Bearer ${token}`,
            },
        })

            .then((res) => {
                if (!res.ok) {
                    throw new Error("Failed to load persons");
                }


                return res.json();

            })
            .then((data) => {
                setPersons(Array.isArray(data) ? data : []);
            })
            .catch((err) => {
                console.error(err);
                setError("Could not load missing persons.");
            });
    }, []);

    return (

        <div className="missing-persons-page">
            <div className="missing-persons-header">
                <h1>Missing Persons</h1>
            </div>

            {error && <p className="alert-banner">{error}</p>}

            {persons.length === 0 && !error && (
                <p>No missing persons found.</p>
            )}

            <div className="missing-persons-grid">
                {[...persons]
                    .sort((firstPerson, secondPerson) =>
                        `${firstPerson.last_name || ""} ${firstPerson.first_name || ""}`
                            .localeCompare(`${secondPerson.last_name || ""} ${secondPerson.first_name || ""}`)
                    )
                    .slice(0, showMorePersons ? 6 : 2)
                    .map((person) => (
                        <article key={person.person_id} className="missing-person-card">
                            <h2>
                                {person.first_name} {person.last_name}
                            </h2>

                            <p>Age: {person.age || "Unknown"}</p>
                            <p>Status: {person.status || "Unknown"}</p>
                            <p>Risk Level: {person.risk_level || "Unknown"}</p>
                            <p>Last Seen: {person.last_seen_location || "Not recorded"}</p>
                            <p>{person.description || "No description recorded."}</p>

                            <button
                                type="button"
                                onClick={() => {
                                    window.location.href = `/persons/${person.person_id}`;
                                }}
                            >
                                View Profile
                            </button>
                        </article>
                    ))}

                {persons.length > 2 && (
                    <button
                        type="button"
                        className="list-toggle-button"
                        onClick={() => setShowMorePersons((current) => !current)}
                    >
                        {showMorePersons ? "Show fewer" : `Show ${Math.min(4, persons.length - 2)} more persons`}
                    </button>
                )}
            </div>
        </div>
    );
}

export default MissingPersonsList;
