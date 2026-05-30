import React, { useEffect, useState } from "react";

function BoloBoard() {
    const [bolos, setBolos] = useState([]);
    const [form, setForm] = useState({
        case_id: "",
        title: "",
        person_name: "",
        last_known_location: "",
        description: "",
        risk_level: "high",
        share_with_partners: false,
        expires_at: "",
    });
    const [message, setMessage] = useState("");

    const token = localStorage.getItem("token");

    const loadBolos = async () => {
        const response = await fetch("http://127.0.0.1:8000/bolos/", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            throw new Error("Could not load BOLO alerts");
        }

        const data = await response.json();
        setBolos(data);
    };

    useEffect(() => {
        loadBolos().catch((err) => {
            console.error(err);
            setMessage("Could not load BOLO alerts");
        });
    }, []);

    const handleChange = (event) => {
        const { name, value, type, checked } = event.target;

        setForm((current) => ({
            ...current,
            [name]: type === "checkbox" ? checked : value,
        }));
    };

    const createBolo = async (event) => {
        event.preventDefault();
        setMessage("");

        const payload = {
            ...form,
            case_id: Number(form.case_id),
            expires_at: form.expires_at || null,
        };

        const response = await fetch("http://127.0.0.1:8000/bolos/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const error = await response.json();
            setMessage(error.detail || "Could not create BOLO alert");
            return;
        }

        setForm({
            case_id: "",
            title: "",
            person_name: "",
            last_known_location: "",
            description: "",
            risk_level: "high",
            share_with_partners: false,
            expires_at: "",
        });

        setMessage("BOLO alert created");
        loadBolos();
    };

    return (
        <div className="bolo-page">
            <div className="bolo-header">
                <h1>BOLO Board</h1>
                <p>Be On The Lookout notices for urgent field coordination.</p>
            </div>

            {message && <p className="alert-banner">{message}</p>}

            <div className="bolo-layout">
                <section className="bolo-panel">
                    <h2>Create BOLO</h2>

                    <form className="bolo-form" onSubmit={createBolo}>
                        <input
                            name="case_id"
                            value={form.case_id}
                            onChange={handleChange}
                            placeholder="Case ID"
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

                        <input
                            type="datetime-local"
                            name="expires_at"
                            value={form.expires_at}
                            onChange={handleChange}
                        />

                        <label className="archive-toggle">
                            <input
                                type="checkbox"
                                name="share_with_partners"
                                checked={form.share_with_partners}
                                onChange={handleChange}
                            />
                            Share with approved partners
                        </label>

                        <button type="submit">Create BOLO</button>
                    </form>
                </section>

                <section className="bolo-panel">
                    <h2>Active BOLO Alerts</h2>

                    <div className="bolo-list">
                        {bolos.length === 0 ? (
                            <p>No active BOLO alerts.</p>
                        ) : (
                            bolos.map((bolo) => (
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
                    </div>
                </section>
            </div>
        </div>
    );
}

export default BoloBoard;
