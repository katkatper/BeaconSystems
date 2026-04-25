import React, { useEffect, useState } from "react";

function Dashboard() {

    const [cases, setCases] = useState([]);

    const [error, setError] = useState(
        localStorage.getItem("token") ? "" : "No login token found. Please log in first."
    );

    useEffect(() => {
        const token = localStorage.getItem("token");

        if (!token) {
            return;
        }


        fetch("http://127.0.0.1:8000/cases/", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        })

            .then((res) => {
                if (!res.ok) {
                    throw new Error("Unauthorized or failed request");
                }
                return res.json();
            })


            .then((data) => {
                console.log("Cases:", data);
                setCases(data);
            })


            .catch((err) => {
                console.error(err);
                setError("Could not load cases");
            });
    }, []);

    return (
        <div>

            <h1>Beacon Dashboard</h1>

            {error && <p>{error}</p>}

            <h2>Cases</h2>
            {cases.length === 0 && !error && <p>No cases found for this user.</p>}
            <ul>
                {cases.map((c) => (

                    <li key={c.case_id}>

                        {c.case_number} - {c.case_status}

                    </li>
                ))}

            </ul>
        </div>
    );
}

export default Dashboard;