import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

function Cases() {
    const [cases, setCases] = useState([]);
    const [editingCaseId, setEditingCaseId] = useState(null);
    const [includeArchived, setIncludeArchived] = useState(false);
    const [message, setMessage] = useState("");
    const [editForm, setEditForm] = useState({
        title: "",
        last_seen_location: "",
        priority_level: "medium",
        case_status: "open",
        investigator_id: "",
        notes: "",
    });

    const role = localStorage.getItem("role");
    const canArchive = role === "admin" || role === "agency_admin";

    const loadCases = async () => {
        const token = localStorage.getItem("token");

        const response = await fetch(
            `http://127.0.0.1:8000/cases/?include_archived=${includeArchived}`,
            {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            }
        );

        if (!response.ok) {
            throw new Error("Failed to load cases");
        }

        const data = await response.json();
        setCases(Array.isArray(data) ? data : []);
    };

    useEffect(() => {
        loadCases().catch((err) => console.error(err));
    }, [includeArchived]);

    const startEdit = (caseItem) => {
        setEditingCaseId(caseItem.case_id);
        setEditForm({
            title: caseItem.title || "",
            last_seen_location: caseItem.last_seen_location || "",
            priority_level: caseItem.priority_level || "medium",
            case_status: caseItem.case_status || "open",
            investigator_id: caseItem.investigator_id || "",
            notes: caseItem.notes || "",
        });
        setMessage("");
    };

    const handleEditChange = (e) => {
        setEditForm({
            ...editForm,
            [e.target.name]: e.target.value,
        });
    };

    const submitUpdate = async (caseId) => {
        const token = localStorage.getItem("token");

        const payload = {
            ...editForm,
            investigator_id: editForm.investigator_id
                ? Number(editForm.investigator_id)
                : null,
        };

        try {
            const response = await fetch(`http://127.0.0.1:8000/cases/${caseId}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                throw new Error("Could not update case");
            }

            setMessage("Case updated.");
            setEditingCaseId(null);
            await loadCases();
        } catch (err) {
            console.error(err);
            setMessage("Could not update case.");
        }
    };

    const archiveCase = async (caseId) => {
        const token = localStorage.getItem("token");

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/cases/${caseId}/archive`,
                {
                    method: "PUT",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Could not archive case");
            }

            setMessage("Case archived.");
            await loadCases();
        } catch (err) {
            console.error(err);
            setMessage(err.message || "Could not archive case.");
        }
    };

    return (
        <div className="cases-page">
            <div className="cases-header">
                <div>
                    <h1>Cases</h1>
                    <p>
                        View assigned cases. Use Case Access for logged access to
                        restricted cases.
                    </p>
                </div>

                <label className="archive-toggle">
                    <input
                        type="checkbox"
                        checked={includeArchived}
                        onChange={(e) => setIncludeArchived(e.target.checked)}
                    />
                    Show archived
                </label>
            </div>

            {message && <p>{message}</p>}

            <div className="case-management-grid">
                {cases.map((caseItem) => {
                    const isEditing = editingCaseId === caseItem.case_id;
                    const isClosed =
                        (caseItem.case_status || "").toLowerCase() === "closed";

                    return (
                        <article key={caseItem.case_id} className="case-management-card">
                            <div className="case-card-header">
                                <div>
                                    <h3>{caseItem.case_number}</h3>
                                    <p>{caseItem.title}</p>
                                </div>
                                <span className="status-badge">
                                    {caseItem.case_status}
                                </span>
                            </div>

                            {isEditing ? (
                                <div className="case-edit-form">
                                    <input
                                        name="title"
                                        placeholder="Title"
                                        value={editForm.title}
                                        onChange={handleEditChange}
                                    />
                                    <input
                                        name="last_seen_location"
                                        placeholder="Last seen location"
                                        value={editForm.last_seen_location}
                                        onChange={handleEditChange}
                                    />
                                    <select
                                        name="priority_level"
                                        value={editForm.priority_level}
                                        onChange={handleEditChange}
                                    >
                                        <option value="low">Low</option>
                                        <option value="medium">Medium</option>
                                        <option value="high">High</option>
                                        <option value="critical">Critical</option>
                                    </select>
                                    <select
                                        name="case_status"
                                        value={editForm.case_status}
                                        onChange={handleEditChange}
                                    >
                                        <option value="open">Open</option>
                                        <option value="investigating">Investigating</option>
                                        <option value="closed">Closed</option>
                                    </select>
                                    <input
                                        name="investigator_id"
                                        type="number"
                                        placeholder="Investigator ID"
                                        value={editForm.investigator_id}
                                        onChange={handleEditChange}
                                    />
                                    <textarea
                                        name="notes"
                                        placeholder="Notes"
                                        value={editForm.notes}
                                        onChange={handleEditChange}
                                    />

                                    <div className="case-actions">
                                        <button onClick={() => submitUpdate(caseItem.case_id)}>
                                            Save
                                        </button>
                                        <button onClick={() => setEditingCaseId(null)}>
                                            Cancel
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <>
                                    <p>Priority: {caseItem.priority_level}</p>
                                    <p>Agency ID: {caseItem.agency_id}</p>
                                    <p>Investigator ID: {caseItem.investigator_id}</p>
                                    <p>Last Seen: {caseItem.last_seen_location}</p>
                                    <p>{caseItem.notes}</p>

                                    <div className="case-actions">
                                        <Link to={`/cases/${caseItem.case_id}`}>
                                            View Case
                                        </Link>
                                        <Link to="/case-access">
                                            Access Restricted Case
                                        </Link>
                                        <button onClick={() => startEdit(caseItem)}>
                                            Update Case
                                        </button>
                                        {canArchive && isClosed && (
                                            <button
                                                onClick={() =>
                                                    archiveCase(caseItem.case_id)
                                                }
                                            >
                                                Archive Closed Case
                                            </button>
                                        )}
                                    </div>
                                </>
                            )}
                        </article>
                    );
                })}
            </div>
        </div>
    );
}

export default Cases;
