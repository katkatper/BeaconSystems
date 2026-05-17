import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

function Cases() {
    const [cases, setCases] = useState([]);

    useEffect(() => {
        const token = localStorage.getItem("token");

        fetch("http://127.0.0.1:8000/cases/", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        })
            .then((res) => res.json())
            .then((data) => setCases(data))
            .catch((err) => console.error(err));
    }, []);

    return (
        <div>
            <h1>Cases</h1>

            {cases.map((caseItem) => (
                <div key={caseItem.case_id}>
                    <h3>{caseItem.case_number}</h3>
                    <p>Status: {caseItem.case_status}</p>
                    <p>Priority: {caseItem.priority_level}</p>
                    <p>Agency ID: {caseItem.agency_id}</p>

                    <Link to={`/cases/${caseItem.case_id}`}>
                        View Case
                    </Link>

                    <hr />
                </div>
            ))}
        </div>
    );
}

export default Cases;