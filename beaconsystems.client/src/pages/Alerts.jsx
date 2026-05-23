import React, { useEffect, useState } from "react";

function Alerts() {
    const [alerts, setAlerts] = useState([]);
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");

    const [form, setForm] = useState({
        case_id: "",
        person_id: "",
        alert_type: "HIGH_CONFIDENCE_SIGHTING",
        title: "",
        description: "",
        severity: "medium",
    });

    const loadAlerts = () => {
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
    };

    useEffect(() => {
        loadAlerts();
    }, []);

    const handleChange = (e) => {
        setForm({
            ...form,
            [e.target.name]: e.target.value,
        });
    };

    const createAlert = async (e) => {
        e.preventDefault();

        const token = localStorage.getItem("token");

        const query = new URLSearchParams({
            case_id: form.case_id,
            person_id: form.person_id,
            alert_type: form.alert_type,
            title: form.title,
            description: form.description,
            severity: form.severity,
        });

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/alerts/?${query.toString()}`,
                {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                throw new Error("Failed to create alert");
            }

            const data = await response.json();

            setMessage(data.message || "Alert created.");

            setForm({
                case_id: "",
                person_id: "",
                alert_type: "HIGH_CONFIDENCE_SIGHTING",
                title: "",
                description: "",
                severity: "medium",
            });

            loadAlerts();
        } catch (err) {
            console.error(err);
            setMessage("Could not create alert.");
        }
    };

    return (
        <div>
            <h1>Operational Alerts</h1>

            {error && <p>{error}</p>}
            {message && <p>{message}</p>}

            <h2>Create Alert</h2>

            <form onSubmit={createAlert}>
                <input
                    name="case_id"
                    type="number"
                    placeholder="Case ID"
                    value={form.case_id}
                    onChange={handleChange}
                />

                <input
                    name="person_id"
                    type="number"
                    placeholder="Person ID"
                    value={form.person_id}
                    onChange={handleChange}
                />

                <input
                    name="title"
                    placeholder="Alert Title"
                    value={form.title}
                    onChange={handleChange}
                />

                <textarea
                    name="description"
                    placeholder="Alert Description"
                    value={form.description}
                    onChange={handleChange}
                />

                <select
                    name="alert_type"
                    value={form.alert_type}
                    onChange={handleChange}
                >
                    <option value="HIGH_CONFIDENCE_SIGHTING">
                        High Confidence Sighting
                    </option>
                    <option value="EVIDENCE_UPLOADED">
                        Evidence Uploaded
                    </option>
                    <option value="CASE_ESCALATION">
                        Case Escalation
                    </option>
                    <option value="GENERAL_ALERT">
                        General Alert
                    </option>
                </select>

                <select
                    name="severity"
                    value={form.severity}
                    onChange={handleChange}
                >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                </select>

                <button type="submit">Create Alert</button>
            </form>

            <hr />

            <h2>Active Alerts</h2>

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
                                alert.severity === "critical"
                                    ? "#ffb3b3"
                                    : alert.severity === "high"
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
                            <strong>Status:</strong> {alert.alert_status}
                        </p>
                    </div>
                ))
            )}
        </div>
    );
}

export default Alerts;