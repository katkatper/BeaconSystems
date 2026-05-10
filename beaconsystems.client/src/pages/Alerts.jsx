import React, { useEffect, useState } from "react";


function Alerts() {

    const [alerts, setAlerts] = useState([]);
    const [error, setError] = useState("");

    useEffect(() => {

        const token = localStorage.getItem("token");

        fetch("http://127.0.0.1:8000/alerts/", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        })
            .then((res) => {

                if (!res.ok) {
                    throw new Error("Failed to load alerts");
                }

                return res.json();
            })
            .then((data) => {
                setAlerts(data);
            })
            .catch((err) => {
                console.error(err);
                setError("Could not load alerts.");
            });

    }, []);

    if (error) {
        return <p>{error}</p>;
    }

    return (
        <div>

            <h1>Operational Alerts</h1>

            {alerts.length === 0 ? (
                <p>No active alerts.</p>
            ) : (
                alerts.map((alert) => (

                    <div
                        key={alert.alert_id}
                        style={{
                            border: "1px solid gray",
                            margin: "12px",
                            padding: "15px",
                            borderRadius: "8px",
                            backgroundColor:
                                alert.severity === "high"
                                    ? "#ffdddd"
                                    : alert.severity === "medium"
                                        ? "#fff4cc"
                                        : "#ddffdd",
                        }}
                    >

                        <h2>{alert.title}</h2>

                        <p>
                            <strong>Type:</strong> {alert.alert_type}
                        </p>

                        <p>
                            <strong>Severity:</strong> {alert.severity}
                        </p>

                        <p>
                            <strong>Description:</strong> {alert.description}
                        </p>

                        <p>
                            <strong>Case ID:</strong> {alert.case_id}
                        </p>

                        <p>
                            <strong>Person ID:</strong> {alert.person_id}
                        </p>

                        <p>
                            <strong>Status:</strong> {alert.status}
                        </p>

                    </div>
                ))
            )}

        </div>
    );
}

export default Alerts;