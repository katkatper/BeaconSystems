import React, { useState } from "react";
import { Link } from "react-router-dom";

function CaseAccess() {
    const [caseId, setCaseId] = useState("");
    const [reasonCategory, setReasonCategory] = useState("assisting_investigator");
    const [reason, setReason] = useState("");
    const [message, setMessage] = useState("");
    const [grantedCaseId, setGrantedCaseId] = useState(null);

    const reasonCategories = [
        ["assisting_investigator", "Assisting assigned investigator"],
        ["shift_coverage", "Shift coverage"],
        ["supervisor_directed", "Supervisor-directed support"],
        ["linked_person_overlap", "Linked person overlap"],
        ["emergency_field_support", "Emergency field support"],
        ["evidence_intake_support", "Evidence intake support"],
        ["court_preparation", "Court/legal preparation"],
        ["other", "Other - supervisor review required"],
    ];

    const submitAccessRequest = async (e) => {
        e.preventDefault();
        const token = localStorage.getItem("token");

        try {
            const response = await fetch("http://127.0.0.1:8000/cases/access-request", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    case_id: Number(caseId),
                    reason_category: reasonCategory,
                    reason,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Access request denied");
            }

            const data = await response.json();
            setMessage(data.message);
            setGrantedCaseId(data.message.includes("auto-approved") ? caseId : null);
        } catch (err) {
            console.error(err);
            setGrantedCaseId(null);
            setMessage(err.message || "Could not request case access.");
        }
    };

    return (
        <div className="case-access-page">
            <div className="case-access-header">
                <h1>Case Access</h1>
            </div>

            <section className="case-access-panel">
                <form className="case-access-form" onSubmit={submitAccessRequest}>
                    <input
                        type="number"
                        placeholder="Case ID"
                        value={caseId}
                        onChange={(e) => setCaseId(e.target.value)}
                        required
                    />

                    <select
                        value={reasonCategory}
                        onChange={(e) => setReasonCategory(e.target.value)}
                        required
                    >
                        {reasonCategories.map(([value, label]) => (
                            <option key={value} value={value}>
                                {label}
                            </option>
                        ))}
                    </select>

                    <textarea
                        placeholder="Explain why this access is needed. Routine reasons may be auto-approved; unusual reasons go to supervisor review."
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        required
                    />

                    <button type="submit">Request Access</button>
                </form>

                {message && <p>{message}</p>}

                {grantedCaseId && (
                    <Link to={`/cases/${grantedCaseId}`}>
                        Open Case {grantedCaseId}
                    </Link>
                )}
            </section>
        </div>
    );
}

export default CaseAccess;
