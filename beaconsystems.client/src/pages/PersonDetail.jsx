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


    return (

        <div>
            <h1>{person.first_name} {person.last_name}</h1>

            <p>Age: {person.age}</p>
            <p>Eye Color: {person.eye_color}</p>
            <p>Hair Color: {person.hair_color}</p>
            <p>Height: {person.height}</p>
            <p>Weight: {person.weight}</p>

            <p>Risk Level: {person.risk_level}</p>
            <p>Status: {person.status}</p>

            <p>Last Seen: {person.last_seen_location}</p>
            <p>Description: {person.description}</p>


            <h2>Related Cases</h2>

            {cases.length === 0 && <p>No cases found.</p>}

            {cases.map((c) => (
                <div key={c.case_id}>
                    <p>Case #: {c.case_number}</p>
                    <p>Status: {c.case_status}</p>

                    <button
                        onClick={() => {
                            window.location.href = `/cases/${c.case_id}`;
                        }}
                    >
                        Open Case
                    </button>
                </div>
            ))}
        </div>
    );
}

export default PersonDetail;