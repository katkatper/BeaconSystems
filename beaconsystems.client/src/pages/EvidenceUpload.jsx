import React, { useEffect, useState } from "react";

function EvidenceUpload() {
    const [caseId, setCaseId] = useState("");
    const [filterCaseId, setFilterCaseId] = useState("");
    const [evidenceType, setEvidenceType] = useState("");
    const [description, setDescription] = useState("");
    const [file, setFile] = useState(null);
    const [evidence, setEvidence] = useState([]);
    const [evidenceChains, setEvidenceChains] = useState({});
    const [message, setMessage] = useState("");

    const loadEvidence = async (caseFilter = filterCaseId) => {
        const token = localStorage.getItem("token");
        const url = caseFilter
            ? `http://127.0.0.1:8000/evidence/?case_id=${caseFilter}`
            : "http://127.0.0.1:8000/evidence/";

        const response = await fetch(url, {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            throw new Error("Failed to load evidence");
        }

        const data = await response.json();
        setEvidence(Array.isArray(data) ? data : []);
    };

    useEffect(() => {
        loadEvidence("").catch((err) => console.error(err));
    }, []);

    const submitEvidence = async (e) => {
        e.preventDefault();

        const token = localStorage.getItem("token");
        const formData = new FormData();

        formData.append("case_id", caseId);
        formData.append("evidence_type", evidenceType);
        formData.append("description", description);
        formData.append("file", file);

        try {
            const response = await fetch(
                "http://127.0.0.1:8000/evidence/upload",
                {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                    body: formData,
                }
            );

            if (!response.ok) {
                throw new Error("Upload failed");
            }

            const data = await response.json();

            setMessage(data.message);
            setEvidenceType("");
            setDescription("");
            setFile(null);
            await loadEvidence(filterCaseId);
        } catch (err) {
            console.error(err);
            setMessage("Could not upload evidence.");
        }
    };

    const viewEvidence = async (evidenceId) => {
        const token = localStorage.getItem("token");

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/evidence/view/${evidenceId}`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                throw new Error("Could not open evidence");
            }

            const blob = await response.blob();
            const fileUrl = window.URL.createObjectURL(blob);
            window.open(fileUrl, "_blank");
        } catch (err) {
            console.error(err);
            alert("Could not open evidence.");
        }
    };

    const loadEvidenceChain = async (evidenceId) => {
        const token = localStorage.getItem("token");

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/evidence/chain/${evidenceId}`,
                {
                    headers: { Authorization: `Bearer ${token}` },
                }
            );

            if (!response.ok) {
                throw new Error("Failed to load chain");
            }

            const data = await response.json();
            setEvidenceChains((prev) => ({
                ...prev,
                [evidenceId]: data,
            }));
        } catch (err) {
            console.error(err);
        }
    };

    const markEvidenceSensitive = async (evidenceId, isSensitive) => {
        const token = localStorage.getItem("token");

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/evidence/${evidenceId}/sensitive?is_sensitive=${isSensitive}`,
                {
                    method: "PUT",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                throw new Error("Could not update sensitivity");
            }

            setEvidence(
                evidence.map((item) =>
                    item.evidence_id === evidenceId
                        ? { ...item, is_sensitive: isSensitive }
                        : item
                )
            );
        } catch (err) {
            console.error(err);
            alert("Could not update evidence sensitivity.");
        }
    };

    return (
        <div className="evidence-page">
            <div className="evidence-header">
                <h1>Evidence</h1>
                <p>Upload, review, open, and track chain of custody records.</p>
            </div>

            <div className="evidence-layout">
                <section className="evidence-panel">
                    <h2>Upload Evidence</h2>

                    <form className="evidence-form" onSubmit={submitEvidence}>
                        <input
                            type="number"
                            placeholder="Case ID"
                            value={caseId}
                            onChange={(e) => setCaseId(e.target.value)}
                            required
                        />

                        <input
                            type="text"
                            placeholder="Evidence Type"
                            value={evidenceType}
                            onChange={(e) => setEvidenceType(e.target.value)}
                            required
                        />

                        <textarea
                            placeholder="Description"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                        />

                        <input
                            type="file"
                            onChange={(e) => setFile(e.target.files[0])}
                            required
                        />

                        <button type="submit">Upload Evidence</button>
                    </form>

                    {message && <p>{message}</p>}
                </section>

                <section className="evidence-panel">
                    <div className="evidence-registry-header">
                        <h2>Evidence Registry</h2>
                        <div className="evidence-filter">
                            <input
                                type="number"
                                placeholder="Filter by Case ID"
                                value={filterCaseId}
                                onChange={(e) => setFilterCaseId(e.target.value)}
                            />
                            <button onClick={() => loadEvidence(filterCaseId)}>
                                Filter
                            </button>
                            <button
                                onClick={() => {
                                    setFilterCaseId("");
                                    loadEvidence("");
                                }}
                            >
                                Clear
                            </button>
                        </div>
                    </div>

                    {evidence.length === 0 ? (
                        <p>No evidence uploaded yet.</p>
                    ) : (
                        <div className="evidence-list">
                            {evidence.map((item) => (
                                <article key={item.evidence_id} className="evidence-card">
                                    <div className="evidence-card-topline">
                                        <strong>{item.file_name || "Unnamed file"}</strong>
                                        {item.is_sensitive && (
                                            <span className="sensitive-badge">
                                                Sensitive
                                            </span>
                                        )}
                                    </div>

                                    <p>Case ID: {item.case_id}</p>
                                    <p>Type: {item.evidence_type}</p>
                                    <p>{item.description || "No description provided"}</p>

                                    <div className="evidence-actions">
                                        <button
                                            onClick={() => viewEvidence(item.evidence_id)}
                                        >
                                            Open File
                                        </button>
                                        <button
                                            onClick={() =>
                                                loadEvidenceChain(item.evidence_id)
                                            }
                                        >
                                            Chain of Custody
                                        </button>
                                        <button
                                            onClick={() =>
                                                markEvidenceSensitive(
                                                    item.evidence_id,
                                                    !item.is_sensitive
                                                )
                                            }
                                        >
                                            {item.is_sensitive
                                                ? "Unmark Sensitive"
                                                : "Mark Sensitive"}
                                        </button>
                                    </div>

                                    {evidenceChains[item.evidence_id]?.map((event) => (
                                        <div
                                            key={event.chain_id}
                                            className="evidence-chain-item"
                                        >
                                            <p><strong>Action:</strong> {event.action}</p>
                                            <p><strong>Details:</strong> {event.details}</p>
                                            <p><strong>Date:</strong> {event.created_at}</p>
                                        </div>
                                    ))}
                                </article>
                            ))}
                        </div>
                    )}
                </section>
            </div>
        </div>
    );
}

export default EvidenceUpload;
