import React, { useEffect, useState } from "react";

const sourceTypes = [
    "hospital",
    "transportation",
    "camera",
    "toll",
    "cell_provider",
    "social_media",
    "ngo",
    "other",
];

function PartnerSources() {
    const [sources, setSources] = useState([]);
    const [externalRecords, setExternalRecords] = useState([]);
    const [message, setMessage] = useState("");
    const [form, setForm] = useState({
        name: "",
        source_type: "hospital",
        api_url: "",
        description: "",
    });

    const loadSources = async () => {
        const token = localStorage.getItem("token");
        const headers = {
            Authorization: `Bearer ${token}`,
        };

        const [sourcesResponse, recordsResponse] = await Promise.all([
            fetch("http://127.0.0.1:8000/integrations/", { headers }),
            fetch("http://127.0.0.1:8000/external-records/", { headers }),
        ]);

        if (!sourcesResponse.ok) {
            throw new Error("Failed to load partner sources");
        }

        const sourcesData = await sourcesResponse.json();
        const recordsData = recordsResponse.ok ? await recordsResponse.json() : [];

        setSources(Array.isArray(sourcesData) ? sourcesData : []);
        setExternalRecords(Array.isArray(recordsData) ? recordsData : []);
    };

    useEffect(() => {
        loadSources().catch((err) => console.error(err));
    }, []);

    const handleChange = (e) => {
        setForm({
            ...form,
            [e.target.name]: e.target.value,
        });
    };

    const submitSource = async (e) => {
        e.preventDefault();
        const token = localStorage.getItem("token");

        try {
            const response = await fetch("http://127.0.0.1:8000/integrations/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(form),
            });

            if (!response.ok) {
                throw new Error("Could not create partner source");
            }

            setMessage("Partner source created and marked pending.");
            setForm({
                name: "",
                source_type: "hospital",
                api_url: "",
                description: "",
            });
            await loadSources();
        } catch (err) {
            console.error(err);
            setMessage("Could not create partner source.");
        }
    };

    const updateSource = async (sourceId, updates) => {
        const token = localStorage.getItem("token");

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/integrations/${sourceId}`,
                {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify(updates),
                }
            );

            if (!response.ok) {
                throw new Error("Could not update partner source");
            }

            await loadSources();
        } catch (err) {
            console.error(err);
            alert("Could not update partner source.");
        }
    };

    return (
        <div className="partner-page">
            <div className="partner-header">
                <h1>Partner Sources</h1>
                <p>
                    Track approved hospitals, transportation partners, cameras, toll
                    systems, cell providers, social platforms, and NGOs.
                </p>
            </div>

            <div className="partner-layout">
                <section className="partner-panel">
                    <h2>Add Partner Source</h2>

                    <form className="partner-form" onSubmit={submitSource}>
                        <input
                            name="name"
                            placeholder="Partner name"
                            value={form.name}
                            onChange={handleChange}
                            required
                        />

                        <select
                            name="source_type"
                            value={form.source_type}
                            onChange={handleChange}
                        >
                            {sourceTypes.map((type) => (
                                <option key={type} value={type}>
                                    {type.replace("_", " ")}
                                </option>
                            ))}
                        </select>

                        <input
                            name="api_url"
                            placeholder="Approved API URL or intake endpoint"
                            value={form.api_url}
                            onChange={handleChange}
                        />

                        <textarea
                            name="description"
                            placeholder="Agreement notes, coverage area, data types, and legal limits"
                            value={form.description}
                            onChange={handleChange}
                        />

                        <button type="submit">Create Source</button>
                    </form>

                    {message && <p>{message}</p>}
                </section>

                <section className="partner-panel">
                    <h2>Source Registry</h2>

                    {sources.length === 0 ? (
                        <p>No partner sources registered yet.</p>
                    ) : (
                        <div className="partner-list">
                            {sources.map((source) => (
                                <article key={source.id} className="partner-card">
                                    {(() => {
                                        const recordCount = externalRecords.filter(
                                            (record) =>
                                                record.integration_source_id === source.id
                                        ).length;

                                        return (
                                            <>
                                    <div className="partner-topline">
                                        <strong>{source.name}</strong>
                                        <span className={`request-status ${source.status}`}>
                                            {source.status}
                                        </span>
                                    </div>

                                    <p>{source.source_type.replace("_", " ")}</p>
                                    <p>{source.description || "No description provided"}</p>
                                    <p>{source.api_url || "No API URL registered"}</p>
                                    <p>
                                        {source.is_active
                                            ? "Active for approved use"
                                            : "Inactive until approved"}
                                    </p>
                                    <p>{recordCount} external records linked</p>

                                    <div className="partner-actions">
                                        <button
                                            onClick={() =>
                                                updateSource(source.id, {
                                                    status: "approved",
                                                    is_active: true,
                                                })
                                            }
                                        >
                                            Approve
                                        </button>
                                        <button
                                            onClick={() =>
                                                updateSource(source.id, {
                                                    status: "suspended",
                                                    is_active: false,
                                                })
                                            }
                                        >
                                            Suspend
                                        </button>
                                        <button
                                            onClick={() =>
                                                updateSource(source.id, {
                                                    status: "revoked",
                                                    is_active: false,
                                                })
                                            }
                                        >
                                            Revoke
                                        </button>
                                    </div>
                                            </>
                                        );
                                    })()}
                                </article>
                            ))}
                        </div>
                    )}
                </section>
            </div>
        </div>
    );
}

export default PartnerSources;
