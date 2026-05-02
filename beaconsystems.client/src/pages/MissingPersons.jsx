import React, { useEffect, useState } from "react";

function MissingPersonsList() {

    const [persons, setPersons] = useState([]);
    const [error, setError] = useState("");

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
                setPersons(data);
            })
            .catch((err) => {
                console.error(err);
                setError("Could not load missing persons.");
            });
    }, []);

    return (

        <div>
            <h1>Missing Persons</h1>

            {error && <p>{error}</p>}

            {persons.length === 0 && !error && (
                <p>No missing persons found.</p>
            )}


            {persons.map((person) => (
                <div
                    key={person.person_id}
                    style={{
                        border: "1px solid gray",
                        padding: "15px",
                        margin: "10px",
                        borderRadius: "8px",
                    }}
                >

                    <h2>
                        {person.first_name} {person.last_name}
                    </h2>

                    <p>Age: {person.age}</p>
                    <p>Status: {person.status}</p>
                    <p>Risk Level: {person.risk_level}</p>
                    <p>Last Seen: {person.last_seen_location}</p>
                    <p>Description: {person.description}</p>

                    <button
                        onClick={() => {
                            window.location.href = `/persons/${person.person_id}`;
                        }}
                    >
                        View Profile
                    </button>

                </div>
            ))}
        </div>
    );
}

export default MissingPersonsList;