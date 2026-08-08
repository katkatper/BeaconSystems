import React, { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

const alertTemplates = [
    ["Sighting", { alert_type: "HIGH_CONFIDENCE_SIGHTING", title: "High Confidence Sighting", severity: "high", alert_source: "witness_tip" }],
    ["Child Missing", { alert_type: "CHILD_MISSING", title: "Child Missing", severity: "critical", alert_source: "supervisor_action" }],
    ["Officer Safety", { alert_type: "OFFICER_SAFETY", title: "Officer Safety Alert", severity: "critical", alert_source: "public_safety_system" }],
    ["Critical Evidence", { alert_type: "CRITICAL_EVIDENCE", title: "Critical Evidence", severity: "critical", alert_source: "investigator" }],
    ["Hospital Match", { alert_type: "HOSPITAL_MATCH", title: "Potential Hospital Match", severity: "high", alert_source: "integration_feed" }],
    ["DNA Match", { alert_type: "DNA_MATCH", title: "DNA Match", severity: "high", alert_source: "data_match_engine" }],
    ["Known Associate Located", { alert_type: "KNOWN_ASSOCIATE_LOCATED", title: "Known Associate Located", severity: "high", alert_source: "investigator" }],
    ["Vehicle Located", { alert_type: "VEHICLE_LOCATED", title: "Vehicle Located", severity: "high", alert_source: "integration_feed" }],
];

function Alerts() {
    const [searchParams] = useSearchParams();
    const isAmberLaunch = searchParams.get("create") === "amber";
    const [alerts, setAlerts] = useState([]);
    const [cases, setCases] = useState([]);
    const [persons, setPersons] = useState([]);
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");
    const [showAllAlerts, setShowAllAlerts] = useState(false);
    const [editingAlertId, setEditingAlertId] = useState(null);

    const [form, setForm] = useState({
        case_id: "",
        person_id: "",
        alert_type: isAmberLaunch ? "AMBER_ALERT" : "HIGH_CONFIDENCE_SIGHTING",
        alert_source: "investigator",
        source_detail: "",
        confidence_score: "",
        title: isAmberLaunch ? "AMBER Alert" : "",
        description: "",
        severity: isAmberLaunch ? "critical" : "medium",
    });
    const [alertEditForm, setAlertEditForm] = useState({
        case_id: "",
        person_id: "",
        alert_type: "HIGH_CONFIDENCE_SIGHTING",
        alert_source: "investigator",
        source_detail: "",
        confidence_score: "",
        title: "",
        description: "",
        severity: "medium",
        alert_status: "active",
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

    useEffect(() => {
        loadAlerts();
        const token = localStorage.getItem("token");
        Promise.all([
            fetch("http://127.0.0.1:8000/cases/", { headers: { Authorization: `Bearer ${token}` } }),
            fetch("http://127.0.0.1:8000/persons/?limit=200", { headers: { Authorization: `Bearer ${token}` } }),
        ]).then(async ([caseResponse, personResponse]) => {
            setCases(caseResponse.ok ? await caseResponse.json() : []);
            setPersons(personResponse.ok ? await personResponse.json() : []);
        }).catch((err) => console.error(err));
    }, []);

    const handleChange = (e) => {
        const { name, value } = e.target;
        if (name === "case_id") {
            const selectedCase = cases.find((caseItem) => String(caseItem.case_id) === value);
            setForm((current) => ({
                ...current,
                case_id: value,
                person_id: selectedCase?.person_id ?? "",
            }));
            return;
        }
        setForm((current) => ({ ...current, [name]: value }));
    };

    const applyAlertTemplate = (template) => {
        setForm((current) => ({
            ...current,
            ...template,
            description: "",
            confidence_score: "",
        }));
    };

    const handleAlertEditChange = (e) => {
        setAlertEditForm({
            ...alertEditForm,
            [e.target.name]: e.target.value,
        });
    };

    const startEditingAlert = (alert) => {
        setEditingAlertId(alert.alert_id);
        setAlertEditForm({
            case_id: alert.case_id ?? "",
            person_id: alert.person_id ?? "",
            alert_type: alert.alert_type || "HIGH_CONFIDENCE_SIGHTING",
            alert_source: alert.alert_source || "investigator",
            source_detail: alert.source_detail || "",
            confidence_score: alert.confidence_score ?? "",
            title: alert.title || "",
            description: alert.description || "",
            severity: alert.severity || "medium",
            alert_status: alert.alert_status || "active",
        });
    };

    const cancelAlertEdit = () => {
        setEditingAlertId(null);
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

    const updateAlert = async (alertId) => {
        const token = localStorage.getItem("token");
        const payload = {
            ...alertEditForm,
            case_id: Number(alertEditForm.case_id),
            person_id: Number(alertEditForm.person_id),
            confidence_score:
                alertEditForm.confidence_score === ""
                    ? null
                    : Number(alertEditForm.confidence_score),
        };

        try {
            const response = await fetch(`http://127.0.0.1:8000/alerts/${alertId}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Failed to update alert");
            }

            setMessage("Alert updated.");
            setEditingAlertId(null);
            loadAlerts();
        } catch (err) {
            console.error(err);
            setMessage(err.message || "Could not update alert.");
        }
    };

    const visibleAlerts = showAllAlerts ? alerts : alerts.slice(0, 2);
    const caseLookup = new Map(cases.map((caseItem) => [Number(caseItem.case_id), caseItem]));
    const personLookup = new Map(persons.map((person) => [Number(person.person_id), person]));
    const alertContextFor = (alert) => {
        const caseItem = caseLookup.get(Number(alert.case_id));
        const person = personLookup.get(Number(alert.person_id || caseItem?.person_id));
        return {
            caseNumber: caseItem?.case_number || `Case ${alert.case_id}`,
            personName: person ? `${person.first_name || ""} ${person.last_name || ""}`.trim() : `Person ${alert.person_id}`,
            location: alert.source_detail || person?.last_seen_location || caseItem?.last_seen_location || "Not recorded",
            assignedTo: caseItem?.investigator_name || (caseItem?.investigator_id ? `Investigator ${caseItem.investigator_id}` : "Unassigned"),
        };
    };
    const displayConfidence = (value) => {
        const score = Number(value);
        if (!Number.isFinite(score)) return "Not scored";
        return `${Math.round(score <= 1 ? score * 100 : score)}%`;
    };

    return (
        <div className="alerts-page">
            <div className="alerts-header">
                <h1>Operational Alerts</h1>
            </div>

            {error && <p>{error}</p>}
            {message && <p>{message}</p>}

            <section className="quick-alert-templates" aria-label="Quick alert templates">
                <div>
                    <span>Quick Alerts</span>
                    <small>One click pre-populates the alert workflow</small>
                </div>
                <div className="quick-alert-template-list">
                    {alertTemplates.map(([label, template]) => (
                        <button key={label} type="button" onClick={() => applyAlertTemplate(template)}>
                            {label}
                        </button>
                    ))}
                </div>
            </section>

            <section className="alerts-panel alerts-bolo-handoff">
                <div>
                    <span>Dedicated workflow</span>
                    <h2>BOLO creation has moved to the BOLO Board</h2>
                    <p>Build vehicle, occupant, photo, distribution, expiration, and approval details in one guided workflow.</p>
                </div>
                <Link to="/bolos">Open BOLO Workflow</Link>
            </section>

            <div className="alerts-paired-layout">
                <section className="alerts-panel">
                    <h2>Create Alert</h2>

                    <form className="alerts-form" onSubmit={createAlert}>
                        <select
                            name="case_id"
                            value={form.case_id}
                            onChange={handleChange}
                            required
                        >
                            <option value="">Select authorized case</option>
                            {cases.map((caseItem) => (
                                <option key={caseItem.case_id} value={caseItem.case_id}>
                                    {caseItem.case_number} · {caseItem.title}
                                </option>
                            ))}
                        </select>

                        <div className="smart-alert-context">
                            <span>Victim / Subject</span>
                            <strong>{form.person_id ? (() => {
                                const selectedPerson = personLookup.get(Number(form.person_id));
                                return selectedPerson ? `${selectedPerson.first_name} ${selectedPerson.last_name}` : `Person ${form.person_id}`;
                            })() : "Select a case"}</strong>
                            <small>Person and investigator context are supplied by the case.</small>
                        </div>

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
                            <option value="AMBER_ALERT">
                                AMBER Alert
                            </option>
                            {alertTemplates.slice(1).map(([, template]) => (
                                <option key={template.alert_type} value={template.alert_type}>{template.title}</option>
                            ))}
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
                                    {editingAlertId === alert.alert_id ? (
                                        <div className="inline-edit-form alert-edit-form">
                                            <input
                                                name="case_id"
                                                type="number"
                                                value={alertEditForm.case_id}
                                                onChange={handleAlertEditChange}
                                                placeholder="Case ID"
                                            />
                                            <input
                                                name="person_id"
                                                type="number"
                                                value={alertEditForm.person_id}
                                                onChange={handleAlertEditChange}
                                                placeholder="Person ID"
                                            />
                                            <input
                                                name="title"
                                                value={alertEditForm.title}
                                                onChange={handleAlertEditChange}
                                                placeholder="Alert Title"
                                            />
                                            <select
                                                name="alert_source"
                                                value={alertEditForm.alert_source}
                                                onChange={handleAlertEditChange}
                                            >
                                                {Object.entries(alertSourceLabels).map(([value, label]) => (
                                                    <option value={value} key={value}>{label}</option>
                                                ))}
                                            </select>
                                            <input
                                                name="source_detail"
                                                value={alertEditForm.source_detail}
                                                onChange={handleAlertEditChange}
                                                placeholder="Who provided it or system name"
                                            />
                                            <input
                                                name="confidence_score"
                                                type="number"
                                                min="0"
                                                max="100"
                                                step="0.1"
                                                value={alertEditForm.confidence_score}
                                                onChange={handleAlertEditChange}
                                                placeholder="Confidence score %"
                                            />
                                            <textarea
                                                name="description"
                                                value={alertEditForm.description}
                                                onChange={handleAlertEditChange}
                                                placeholder="Alert Description"
                                            />
                                            <select
                                                name="alert_type"
                                                value={alertEditForm.alert_type}
                                                onChange={handleAlertEditChange}
                                            >
                                                <option value="HIGH_CONFIDENCE_SIGHTING">High Confidence Sighting</option>
                                                <option value="EVIDENCE_UPLOADED">Evidence Uploaded</option>
                                                <option value="CASE_ESCALATION">Case Escalation</option>
                                                <option value="GENERAL_ALERT">General Alert</option>
                                            </select>
                                            <select
                                                name="severity"
                                                value={alertEditForm.severity}
                                                onChange={handleAlertEditChange}
                                            >
                                                <option value="low">Low</option>
                                                <option value="medium">Medium</option>
                                                <option value="high">High</option>
                                                <option value="critical">Critical</option>
                                            </select>
                                            <select
                                                name="alert_status"
                                                value={alertEditForm.alert_status}
                                                onChange={handleAlertEditChange}
                                            >
                                                <option value="active">Active</option>
                                                <option value="reviewed">Reviewed</option>
                                                <option value="closed">Closed</option>
                                            </select>
                                            <div className="inline-edit-actions">
                                                <button type="button" onClick={() => updateAlert(alert.alert_id)}>
                                                    Save Alert
                                                </button>
                                                <button type="button" onClick={cancelAlertEdit}>
                                                    Cancel
                                                </button>
                                            </div>
                                        </div>
                                    ) : (
                                        <>
                                            <div className="alert-card-topline">
                                                <span className={`alert-severity-banner ${alert.severity}`}>
                                                    {alert.severity}
                                                </span>
                                                <h3>{alert.title}</h3>
                                            </div>
                                            <div className="alert-command-summary">
                                                {[
                                                    ["Case", alertContextFor(alert).caseNumber],
                                                    ["Victim / Subject", alertContextFor(alert).personName],
                                                    ["Location", alertContextFor(alert).location],
                                                    ["Reported", alert.created_at ? new Date(alert.created_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }) : "Not recorded"],
                                                    ["Confidence", displayConfidence(alert.confidence_score)],
                                                    ["Assigned To", alertContextFor(alert).assignedTo],
                                                ].map(([label, value]) => (
                                                    <div key={label}><span>{label}</span><strong>{value}</strong></div>
                                                ))}
                                            </div>
                                            <p className="alert-card-description">{alert.description}</p>
                                            <small className="alert-card-source">
                                                {alertSourceLabels[alert.alert_source] || "Source not recorded"}
                                            </small>

                                            <button
                                                type="button"
                                                className="small-secondary-button"
                                                onClick={() => startEditingAlert(alert)}
                                            >
                                                Edit Alert
                                            </button>
                                        </>
                                    )}
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

        </div>
    );
}

export default Alerts;
