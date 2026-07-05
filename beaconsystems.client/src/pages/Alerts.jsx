import React, { useEffect, useState } from "react";

function Alerts() {
    const [alerts, setAlerts] = useState([]);
    const [bolos, setBolos] = useState([]);
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");
    const [showAllAlerts, setShowAllAlerts] = useState(false);
    const [showAllBolos, setShowAllBolos] = useState(false);

    const [form, setForm] = useState({
        case_id: "",
        person_id: "",
        alert_type: "HIGH_CONFIDENCE_SIGHTING",
        alert_source: "investigator",
        source_detail: "",
        confidence_score: "",
        title: "",
        description: "",
        severity: "medium",
    });
    const [boloForm, setBoloForm] = useState({
        case_id: "",
        title: "",
        person_name: "",
        last_known_location: "",
        description: "",
        risk_level: "high",
        share_with_partners: false,
        expires_at: "",
    });
    const alertSourceLabels = {
        investigator: "Investigator lead",
        witness_tip: "Witness tip",
        external_agency: "External agency",
        external_record: "External record match",
        data_match_engine: "Data match engine",
        geofence_event: "Geofence event",
        supervisor_action: "Supervisor action",
        timeline_event: "Timeline event",
        integration_feed: "Integration feed",
        public_safety_system: "Public safety system",
    };

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

    const loadBolos = () => {
        const token = localStorage.getItem("token");

        fetch("http://127.0.0.1:8000/bolos/", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        })
            .then((res) => {
                if (!res.ok) {
                    throw new Error("Failed to load BOLOs");
                }

                return res.json();
            })
            .then((data) => {
                setBolos(data);
            })
            .catch((err) => {
                console.error(err);
                setError("Could not load operational alerts.");
            });
    };

    useEffect(() => {
        loadAlerts();
        loadBolos();
    }, []);

    const handleChange = (e) => {
        setForm({
            ...form,
            [e.target.name]: e.target.value,
        });
    };

    const handleBoloChange = (e) => {
        const { name, value, type, checked } = e.target;

        setBoloForm({
            ...boloForm,
            [name]: type === "checkbox" ? checked : value,
        });
    };

    const createAlert = async (e) => {
        e.preventDefault();

        const token = localStorage.getItem("token");

        const query = new URLSearchParams({
            case_id: form.case_id,
            person_id: form.person_id,
            alert_type: form.alert_type,
            alert_source: form.alert_source,
            source_detail: form.source_detail,
            title: form.title,
            description: form.description,
            severity: form.severity,
        });

        if (form.confidence_score !== "") {
            query.set("confidence_score", form.confidence_score);
        }

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
                alert_source: "investigator",
                source_detail: "",
                confidence_score: "",
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

    const createBolo = async (e) => {
        e.preventDefault();

        const token = localStorage.getItem("token");
        const payload = {
            ...boloForm,
            case_id: boloForm.case_id.trim(),
            expires_at: boloForm.expires_at || null,
        };

        try {
            const response = await fetch("http://127.0.0.1:8000/bolos/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const detail = Array.isArray(errorData.detail)
                    ? errorData.detail.map((item) => item.msg).join("; ")
                    : errorData.detail;

                throw new Error(detail || "Failed to create BOLO");
            }

            setMessage("BOLO created and added to operational alerts.");
            setBoloForm({
                case_id: "",
                title: "",
                person_name: "",
                last_known_location: "",
                description: "",
                risk_level: "high",
                share_with_partners: false,
                expires_at: "",
            });
            loadBolos();
        } catch (err) {
            console.error(err);
            setMessage(err.message || "Could not create BOLO.");
        }
    };
    const visibleAlerts = showAllAlerts ? alerts : alerts.slice(0, 2);
    const visibleBolos = showAllBolos ? bolos : bolos.slice(0, 2);

    return (
        <div className="alerts-page">
            <div className="alerts-header">
                <h1>Operational Alerts</h1>
            </div>

            {error && <p>{error}</p>}
            {message && <p>{message}</p>}

            <div className="alerts-paired-layout">
                <section className="alerts-panel">
                    <h2>Create Alert</h2>

                    <form className="alerts-form" onSubmit={createAlert}>
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

                        <select
                            name="alert_source"
                            value={form.alert_source}
                            onChange={handleChange}
                        >
                            <option value="investigator">Investigator lead</option>
                            <option value="witness_tip">Witness tip</option>
                            <option value="external_agency">External agency</option>
                            <option value="external_record">External record match</option>
                            <option value="data_match_engine">Data match engine</option>
                            <option value="geofence_event">Geofence event</option>
                            <option value="supervisor_action">Supervisor action</option>
                            <option value="timeline_event">Timeline event</option>
                            <option value="integration_feed">Integration feed</option>
                            <option value="public_safety_system">Public safety system</option>
                        </select>

                        <input
                            name="source_detail"
                            placeholder="Who provided it or system name"
                            value={form.source_detail}
                            onChange={handleChange}
                        />

                        <input
                            name="confidence_score"
                            type="number"
                            min="0"
                            max="100"
                            step="0.1"
                            placeholder="Confidence score %"
                            value={form.confidence_score}
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
                </section>

                <section className="alerts-panel">
                    <h2>Active Alerts</h2>

                    {alerts.length === 0 ? (
                        <p>No active alerts.</p>
                    ) : (
                        <div className="alerts-list">
                            {visibleAlerts.map((alert) => (
                                <article
                                    key={alert.alert_id}
                                    className={`alert-card alert-card-${alert.severity}`}
                                >
                                    <div className="alert-card-topline">
                                        <h3>{alert.title}</h3>
                                        <span>{alert.severity}</span>
                                    </div>

                                    <p>
                                        <strong>Type:</strong> {alert.alert_type}
                                    </p>

                                    <p>
                                        <strong>Source:</strong> {alertSourceLabels[alert.alert_source] || "Not recorded"}
                                        {alert.source_detail ? ` | ${alert.source_detail}` : ""}
                                    </p>

                                    {alert.confidence_score !== null && alert.confidence_score !== undefined && (
                                        <p>
                                            <strong>Confidence:</strong> {alert.confidence_score}%
                                        </p>
                                    )}

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
                                </article>
                            ))}
                        </div>
                    )}

                    {alerts.length > 2 && (
                        <button
                            type="button"
                            className="alerts-show-more"
                            onClick={() => setShowAllAlerts((current) => !current)}
                        >
                            {showAllAlerts ? "Show Less" : `Show ${alerts.length - 2} More Alerts`}
                        </button>
                    )}
                </section>
            </div>

            <div className="alerts-paired-layout">
                <section className="alerts-panel">
                    <h2>Create BOLO</h2>

                    <form className="bolo-form" onSubmit={createBolo}>
                        <input
                            name="case_id"
                            value={boloForm.case_id}
                            onChange={handleBoloChange}
                            placeholder="Case ID"
                            required
                        />

                        <input
                            name="title"
                            value={boloForm.title}
                            onChange={handleBoloChange}
                            placeholder="BOLO Title"
                            required
                        />

                        <input
                            name="person_name"
                            value={boloForm.person_name}
                            onChange={handleBoloChange}
                            placeholder="Person Name"
                        />

                        <input
                            name="last_known_location"
                            value={boloForm.last_known_location}
                            onChange={handleBoloChange}
                            placeholder="Last Known Location"
                        />

                        <textarea
                            name="description"
                            value={boloForm.description}
                            onChange={handleBoloChange}
                            placeholder="BOLO Description"
                            required
                        />

                        <select
                            name="risk_level"
                            value={boloForm.risk_level}
                            onChange={handleBoloChange}
                        >
                            <option value="critical">Critical</option>
                            <option value="high">High</option>
                            <option value="medium">Medium</option>
                            <option value="low">Low</option>
                        </select>

                        <input
                            type="datetime-local"
                            name="expires_at"
                            value={boloForm.expires_at}
                            onChange={handleBoloChange}
                        />

                        <label className="archive-toggle">
                            <input
                                type="checkbox"
                                name="share_with_partners"
                                checked={boloForm.share_with_partners}
                                onChange={handleBoloChange}
                            />
                            Share with approved partners
                        </label>

                        <button type="submit">Create BOLO</button>
                    </form>
                </section>

                <section className="alerts-panel">
                    <h2>Active BOLOs</h2>

                    {bolos.length === 0 ? (
                        <p>No active BOLO alerts.</p>
                    ) : (
                        <div className="bolo-list">
                            {visibleBolos.map((bolo) => (
                                <article key={bolo.bolo_id} className="bolo-card">
                                    <div className="bolo-card-topline">
                                        <strong>{bolo.title}</strong>
                                        <span className={`priority-badge priority-${bolo.risk_level}`}>
                                            {bolo.risk_level}
                                        </span>
                                    </div>
                                    <p>{bolo.description}</p>
                                    <small>
                                        Case {bolo.case_id}
                                        {bolo.person_name ? ` | ${bolo.person_name}` : ""}
                                        {bolo.last_known_location
                                            ? ` | ${bolo.last_known_location}`
                                            : ""}
                                        {bolo.expires_at
                                            ? ` | Expires ${new Date(bolo.expires_at).toLocaleString()}`
                                            : ""}
                                    </small>
                                </article>
                            ))}
                        </div>
                    )}

                    {bolos.length > 2 && (
                        <button
                            type="button"
                            className="alerts-show-more"
                            onClick={() => setShowAllBolos((current) => !current)}
                        >
                            {showAllBolos ? "Show Less" : `Show ${bolos.length - 2} More BOLOs`}
                        </button>
                    )}
                </section>
            </div>
        </div>
    );
}

export default Alerts;
