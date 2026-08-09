import React, { useEffect, useState } from "react";
import { apiUrl } from "../api.jsx";

const distributionOptions = [
    "Patrol", "Detectives", "Supervisors", "Dispatch", "State Police",
    "Partner Agencies", "FBI", "Fusion Center", "Crime Lab",
    "Medical Examiner", "Hospitals",
];

const fetchBolos = async (token) => {
    const response = await fetch(apiUrl("/bolos/"), {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });

    if (!response.ok) {
        throw new Error("Could not load BOLO alerts");
    }

    return response.json();
};

function BoloBoard() {
    const [bolos, setBolos] = useState([]);
    const [showMoreBolos, setShowMoreBolos] = useState(false);
    const [form, setForm] = useState({
        case_id: "",
        title: "",
        person_name: "",
        last_known_location: "",
        description: "",
        vehicle: "",
        occupants: "",
        photo_url: "",
        risk_level: "high",
        distribution: ["Patrol", "Detectives", "Supervisors", "Dispatch"],
        expires_at: "",
        approving_supervisor: "",
        approval_confirmed: false,
    });
    const [message, setMessage] = useState("");

    const token = localStorage.getItem("token");

    const loadBolos = async () => {
        const data = await fetchBolos(token);
        setBolos(data);
    };

    useEffect(() => {
        let isMounted = true;

        fetchBolos(token)
            .then((data) => {
                if (isMounted) {
                    setBolos(data);
                }
            })
            .catch((err) => {
                console.error(err);

                if (isMounted) {
                    setMessage("Could not load BOLO alerts");
                }
            });

        return () => {
            isMounted = false;
        };
    }, [token]);

    const handleChange = (event) => {
        const { name, value, type, checked } = event.target;

        setForm((current) => ({
            ...current,
            [name]: type === "checkbox" ? checked : value,
        }));
    };

    const toggleDistribution = (recipient) => {
        setForm((current) => ({
            ...current,
            distribution: current.distribution.includes(recipient)
                ? current.distribution.filter((item) => item !== recipient)
                : [...current.distribution, recipient],
        }));
    };

    const createBolo = async (event) => {
        event.preventDefault();
        setMessage("");

        const partnerRecipients = ["State Police", "Partner Agencies", "FBI", "Fusion Center", "Crime Lab", "Medical Examiner", "Hospitals"];
        const structuredDescription = [
            form.description,
            form.vehicle && `Vehicle: ${form.vehicle}`,
            form.occupants && `Occupants: ${form.occupants}`,
            form.photo_url && `Photo: ${form.photo_url}`,
            `Distribution: ${form.distribution.join(", ") || "No recipients selected"}`,
            `Approval: ${form.approval_confirmed ? `Confirmed by ${form.approving_supervisor || "supervisor"}` : "Not confirmed"}`,
        ].filter(Boolean).join("\n\n");
        const payload = {
            case_id: form.case_id.trim(),
            title: form.title,
            person_name: form.person_name,
            last_known_location: form.last_known_location,
            description: structuredDescription,
            risk_level: form.risk_level,
            share_with_partners: form.distribution.some((recipient) => partnerRecipients.includes(recipient)),
            expires_at: form.expires_at || null,
        };

        const response = await fetch(apiUrl("/bolos/"), {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const error = await response.json();
            const detail = Array.isArray(error.detail)
                ? error.detail.map((item) => item.msg).join("; ")
                : error.detail;
            setMessage(detail || "Could not create BOLO alert");
            return;
        }

        setForm({
            case_id: "",
            title: "",
            person_name: "",
            last_known_location: "",
            description: "",
            vehicle: "",
            occupants: "",
            photo_url: "",
            risk_level: "high",
            distribution: ["Patrol", "Detectives", "Supervisors", "Dispatch"],
            expires_at: "",
            approving_supervisor: "",
            approval_confirmed: false,
        });

        setMessage("BOLO alert created");
        loadBolos();
    };

    return (
        <div className="bolo-page">
            <div className="bolo-header">
                <h1>BOLO Board</h1>
            </div>

            {message && <p className="alert-banner">{message}</p>}

            <div className="bolo-layout">
                <section className="bolo-panel">
                    <h2>Create BOLO</h2>

                    <form className="bolo-form bolo-workflow-form" onSubmit={createBolo}>
                        <fieldset>
                            <legend>General Information</legend>
                        <input
                            name="case_id"
                            value={form.case_id}
                            onChange={handleChange}
                            placeholder="Case ID or case number"
                            required
                        />

                        <input
                            name="title"
                            value={form.title}
                            onChange={handleChange}
                            placeholder="BOLO Title"
                            required
                        />

                        <input
                            name="person_name"
                            value={form.person_name}
                            onChange={handleChange}
                            placeholder="Person Name"
                        />

                        <input
                            name="last_known_location"
                            value={form.last_known_location}
                            onChange={handleChange}
                            placeholder="Last Known Location"
                        />

                        <textarea
                            name="description"
                            value={form.description}
                            onChange={handleChange}
                            placeholder="Description"
                            required
                        />

                        <select
                            name="risk_level"
                            value={form.risk_level}
                            onChange={handleChange}
                        >
                            <option value="critical">Critical</option>
                            <option value="high">High</option>
                            <option value="medium">Medium</option>
                            <option value="low">Low</option>
                        </select>
                        </fieldset>

                        <fieldset>
                            <legend>Vehicle</legend>
                            <textarea name="vehicle" value={form.vehicle} onChange={handleChange} placeholder="Year, make, model, color, plate, VIN, distinguishing features" />
                        </fieldset>

                        <fieldset>
                            <legend>Occupants</legend>
                            <textarea name="occupants" value={form.occupants} onChange={handleChange} placeholder="Names, descriptions, roles, cautions, and known associates" />
                        </fieldset>

                        <fieldset>
                            <legend>Photo</legend>
                            <input name="photo_url" value={form.photo_url} onChange={handleChange} placeholder="Approved photo or secure file URL" />
                        </fieldset>

                        <fieldset>
                            <legend>Distribution · Send To</legend>
                            <div className="bolo-distribution-grid">
                                {distributionOptions.map((recipient) => (
                                    <label key={recipient}>
                                        <input
                                            type="checkbox"
                                            checked={form.distribution.includes(recipient)}
                                            onChange={() => toggleDistribution(recipient)}
                                        />
                                        {recipient}
                                    </label>
                                ))}
                            </div>
                        </fieldset>

                        <fieldset>
                            <legend>Expiration</legend>
                        <input
                            type="datetime-local"
                            name="expires_at"
                            value={form.expires_at}
                            onChange={handleChange}
                        />
                        </fieldset>

                        <fieldset>
                            <legend>Approvals</legend>
                            <input
                                name="approving_supervisor"
                                value={form.approving_supervisor}
                                onChange={handleChange}
                                placeholder="Approving supervisor"
                            />
                        <label className="archive-toggle">
                            <input
                                type="checkbox"
                                name="approval_confirmed"
                                checked={form.approval_confirmed}
                                onChange={handleChange}
                                required
                            />
                            Approval and distribution reviewed
                        </label>
                        </fieldset>

                        <button type="submit">Approve &amp; Distribute BOLO</button>
                    </form>
                </section>

                <section className="bolo-panel">
                    <h2>Active BOLO Alerts</h2>

                    <div className="bolo-list">
                        {bolos.length === 0 ? (
                            <p>No active BOLO alerts.</p>
                        ) : (
                            bolos.slice(0, showMoreBolos ? 6 : 2).map((bolo) => (
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
                                        {bolo.expires_at ? ` | Expires ${new Date(bolo.expires_at).toLocaleString()}` : ""}
                                    </small>
                                </article>
                            ))
                        )}
                        {bolos.length > 2 && (
                            <button
                                type="button"
                                className="list-toggle-button"
                                onClick={() => setShowMoreBolos((current) => !current)}
                            >
                                {showMoreBolos ? "Show fewer" : `Show ${Math.min(4, bolos.length - 2)} more BOLOs`}
                            </button>
                        )}
                    </div>
                </section>
            </div>
        </div>
    );
}

export default BoloBoard;
