import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";


function Dashboard() {
    const [cases, setCases] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [summary, setSummary] = useState(null);
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
        fetch("http://127.0.0.1:8000/dashboard/summary", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        })
            .then((res) => {
                if (!res.ok) {
                    throw new Error("Failed to load dashboard summary");
                }
                return res.json();
            })
            .then((data) => {
                setSummary(data);
            })
            .catch((err) => {
                console.error(err);
            });

        const interval = setInterval(() => {

            fetch("http://127.0.0.1:8000/dashboard/summary", {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            })
                .then((res) => res.json())
                .then((data) => {
                    setSummary(data);
                })
                .catch((err) => {
                    console.error(err);
                });

        }, 10000);

        fetch("http://127.0.0.1:8000/alerts/", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        })
            .then((res) => res.json())
            .then((data) => setAlerts(data))
            .catch((err) => console.error(err));

        return () => clearInterval(interval);


    }, []);

    const updateCaseStatus = async (caseId, newStatus) => {
        const token = localStorage.getItem("token");

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/cases/${caseId}`,
                {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({
                        case_status: newStatus,
                    }),
                }
            );

            if (!response.ok) {
                throw new Error("Update failed");
            }

            setCases(
                cases.map((c) =>
                    c.case_id === caseId
                        ? { ...c, case_status: newStatus }
                        : c
                )
            );
        } catch (err) {
            console.error(err);
            setError("Could not update case");
        }
    };
    const deleteCase = async (caseId) => {
        const token = localStorage.getItem("token");

        if (!window.confirm("Delete this case?")) {
            return;
        }

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/cases/${caseId}`,
                {
                    method: "DELETE",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                throw new Error("Delete failed");
            }

            setCases(
                cases.filter(
                    c => c.case_id !== caseId
                )
            );

        } catch (err) {
            console.error(err);
            setError("Could not delete case");
        }
    };
    return (
        <div className="dashboard-page">

            <div className="dashboard-header">
                <h1>Beacon Command Center</h1>

                <p>
                    Real-time investigative intelligence and operational coordination
                </p>
            </div>

            {summary && (

                <div className="command-grid">

                    <div className="command-card">
                        <h3>Total Cases</h3>
                        <p>{summary.total_cases}</p>
                    </div>

                    <div className="command-card">
                        <h3>Open Cases</h3>
                        <p>{summary.open_cases}</p>
                    </div>

                    <div className="command-card">
                        <h3>High Priority</h3>
                        <p>{summary.high_priority_cases}</p>
                    </div>

                </div>
            )}

            {error && <p>{error}</p>}

            {alerts
                .filter((alert) => alert.severity === "high" || alert.severity === "critical")
                .map((alert) => (
                    <div key={alert.alert_id} className={`alert-banner alert-${alert.severity}`}>
                        <strong>{alert.severity.toUpperCase()} ALERT:</strong> {alert.title}
                        <p>{alert.description}</p>
                    </div>
                ))}

            <h2 className="section-title">
                Active Cases
            </h2>

            {cases.length === 0 && !error && (
                <p>No cases found for this user.</p>
            )}

            <div className="cases-grid">

                {cases.map((c) => (

                    <div
                        key={c.case_id}
                        className="case-card"
                    >

                        <div className="case-card-header">

                            <span
                                className={`priority-badge priority-${c.priority_level}`}
                            >
                                {c.priority_level}
                            </span>

                            <span className="status-badge">
                                {c.case_status}
                            </span>

                        </div>

                        <h3>
                            <Link to={`/cases/${c.case_id}`}>
                                {c.case_number}
                            </Link>
                        </h3>

                        <p>
                            Last Seen: {c.last_seen_location}
                        </p>

                        <p>
                            Priority: {c.priority_level}
                        </p>

                        <button
                            onClick={() =>
                                updateCaseStatus(
                                    c.case_id,
                                    "investigating"
                                )
                            }
                        >
                            Investigating
                        </button>

                        <button
                            onClick={() =>
                                updateCaseStatus(
                                    c.case_id,
                                    "closed"
                                )
                            }
                        >
                            Close Case
                        </button>

                        <button
                            onClick={() =>
                                deleteCase(c.case_id)
                            }
                        >
                            Delete Case
                        </button>

                    </div>

                ))}

            </div>

        </div>
    );
}
    export default Dashboard;
