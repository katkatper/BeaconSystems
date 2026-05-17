import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";


function Dashboard() {
    const [cases, setCases] = useState([]);
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
        <div>
            <h1>Beacon Dashboard</h1>

            {summary && (
                <div style={styles.summaryGrid}>
                    <div style={styles.summaryCard}>
                        <h3>Total Cases</h3>
                        <p>{summary.total_cases}</p>
                    </div>

                    <div style={styles.summaryCard}>
                        <h3>Open Cases</h3>
                        <p>{summary.open_cases}</p>
                    </div>

                    <div style={styles.summaryCard}>
                        <h3>High Priority</h3>
                        <p>{summary.high_priority_cases}</p>
                    </div>
                </div>
            )}

            {summary && (
                <div>
                    <h2>Recent Sightings</h2>

                    {summary.recent_sightings?.length === 0 ? (
                        <p>No recent sightings.</p>
                    ) : (
                        summary.recent_sightings?.map((sighting) => (
                            <div key={sighting.sighting_id} style={styles.infoCard}>
                                <strong>{sighting.location}</strong>
                                <p>{sighting.description}</p>
                                <p>Confidence: {sighting.confidence_score ?? "Unknown"}</p>
                            </div>
                        ))
                    )}

                    <h2>Recent Activity</h2>

                    {summary.recent_activity?.length === 0 ? (
                        <p>No recent activity.</p>
                    ) : (
                        summary.recent_activity?.map((activity) => (
                            <div key={activity.id} style={styles.infoCard}>
                                <strong>{activity.action}</strong>
                                <p>{activity.details}</p>
                                <p>{activity.timestamp}</p>
                            </div>
                        ))
                    )}
                </div>
            )
            }

            {error && <p>{error}</p>}

            <h2>Active Cases</h2>

            {cases.length === 0 && !error && (
                <p>No cases found for this user.</p>
            )}

            <div>
                {cases.map((c) => (
                    <div
                        key={c.case_id}
                        style={{
                            border: "1px solid gray",
                            padding: "15px",
                            margin: "10px",
                            borderRadius: "8px",
                        }}
                    >
                        <h3>
                            <Link to={`/cases/${c.case_id}`}>
                                {c.case_number}
                            </Link>
                        </h3>

                        <p>Status: {c.case_status}</p>

                        <p>Last Seen: {c.last_seen_location}</p>

                        <p>Priority: {c.priority_level}</p>

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
    )

};
const styles = {
    summaryGrid: {
        display: "flex",
        gap: "15px",
        margin: "20px 0",
        flexWrap: "wrap",
    },

    summaryCard: {
        border: "1px solid gray",
        padding: "15px",
        borderRadius: "8px",
        minWidth: "160px",
        backgroundColor: "#f5f5f5",
    },

    infoCard: {
        border: "1px solid gray",
        padding: "12px",
        margin: "10px 0",
        borderRadius: "8px",
    },

};
  export default Dashboard;