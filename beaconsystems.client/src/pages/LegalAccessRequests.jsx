import React, { useEffect, useState } from "react";

const authorityTypes = [
    "agency_agreement",
    "warrant",
    "subpoena",
    "court_order",
    "consent",
    "approved_api",
    "partner_integration",
];

const sourceTypes = [
    "hospital",
    "transportation",
    "camera",
    "toll",
    "cell_provider",
    "social_media",
    "other",
];

function LegalAccessRequests() {
    const [requests, setRequests] = useState([]);
    const [message, setMessage] = useState("");
    const [reviewNotes, setReviewNotes] = useState({});
    const [form, setForm] = useState({
        case_id: "",
        requester_name: "",
        requester_organization: "",
        requester_role: "district_attorney",
        contact_email: "",
        authority_type: "court_order",
        source_type: "hospital",
        target_identifier: "",
        jurisdiction: "",
        legal_reference: "",
        purpose: "",
        scope_description: "",
        minimization_plan: "",
        retention_plan: "",
        document_location: "",
    });

    const loadRequests = async () => {
        const token = localStorage.getItem("token");

        const response = await fetch("http://127.0.0.1:8000/legal-access/", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            throw new Error("Failed to load legal access requests");
        }

        const data = await response.json();
        setRequests(Array.isArray(data) ? data : []);
    };

    useEffect(() => {
        loadRequests().catch((err) => console.error(err));
    }, []);

    const handleChange = (e) => {
        setForm({
            ...form,
            [e.target.name]: e.target.value,
        });
    };

    const submitRequest = async (e) => {
        e.preventDefault();
        const token = localStorage.getItem("token");

        const payload = {
            ...form,
            case_id: form.case_id ? Number(form.case_id) : null,
        };

        try {
            const response = await fetch("http://127.0.0.1:8000/legal-access/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                throw new Error("Could not submit legal access request");
            }

            setMessage("Legal access request submitted for review.");
            setForm({
                ...form,
                target_identifier: "",
                legal_reference: "",
                purpose: "",
                scope_description: "",
                minimization_plan: "",
                retention_plan: "",
                document_location: "",
            });
            await loadRequests();
        } catch (err) {
            console.error(err);
            setMessage("Could not submit legal access request.");
        }
    };

    const reviewRequest = async (requestId, status) => {
        const token = localStorage.getItem("token");

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/legal-access/${requestId}/review`,
                {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({
                        status,
                        review_notes: reviewNotes[requestId] || "",
                    }),
                }
            );

            if (!response.ok) {
                throw new Error("Could not review request");
            }

            await loadRequests();
        } catch (err) {
            console.error(err);
            alert("Could not update request status.");
        }
    };

    return (
        <div className="legal-access-page">
            <div className="legal-access-header">
                <h1>Legal Access Requests</h1>
                <p>
                    Submit and review authority documents before Beacon obtains live
                    data from external partners.
                </p>
            </div>

            <div className="legal-access-layout">
                <section className="legal-panel">
                    <h2>Submit Authority Package</h2>

                    <form className="legal-form" onSubmit={submitRequest}>
                        <input
                            name="case_id"
                            placeholder="Case ID"
                            value={form.case_id}
                            onChange={handleChange}
                        />
                        <input
                            name="requester_name"
                            placeholder="Requester name"
                            value={form.requester_name}
                            onChange={handleChange}
                            required
                        />
                        <input
                            name="requester_organization"
                            placeholder="Court, DA office, agency, or partner"
                            value={form.requester_organization}
                            onChange={handleChange}
                            required
                        />
                        <input
                            name="requester_role"
                            placeholder="Requester role"
                            value={form.requester_role}
                            onChange={handleChange}
                            required
                        />
                        <input
                            name="contact_email"
                            placeholder="Contact email"
                            value={form.contact_email}
                            onChange={handleChange}
                        />

                        <select
                            name="authority_type"
                            value={form.authority_type}
                            onChange={handleChange}
                        >
                            {authorityTypes.map((type) => (
                                <option key={type} value={type}>
                                    {type.replace("_", " ")}
                                </option>
                            ))}
                        </select>

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
                            name="target_identifier"
                            placeholder="Target identifier or subject"
                            value={form.target_identifier}
                            onChange={handleChange}
                        />
                        <input
                            name="jurisdiction"
                            placeholder="Jurisdiction"
                            value={form.jurisdiction}
                            onChange={handleChange}
                        />
                        <input
                            name="legal_reference"
                            placeholder="Warrant, subpoena, order, or agreement number"
                            value={form.legal_reference}
                            onChange={handleChange}
                        />
                        <input
                            name="document_location"
                            placeholder="Document location or secure evidence path"
                            value={form.document_location}
                            onChange={handleChange}
                        />

                        <textarea
                            name="purpose"
                            placeholder="Purpose for requested access"
                            value={form.purpose}
                            onChange={handleChange}
                            required
                        />
                        <textarea
                            name="scope_description"
                            placeholder="Requested scope, date range, data fields, and limits"
                            value={form.scope_description}
                            onChange={handleChange}
                            required
                        />
                        <textarea
                            name="minimization_plan"
                            placeholder="Minimization plan"
                            value={form.minimization_plan}
                            onChange={handleChange}
                        />
                        <textarea
                            name="retention_plan"
                            placeholder="Retention and deletion plan"
                            value={form.retention_plan}
                            onChange={handleChange}
                        />

                        <button type="submit">Submit for Review</button>
                    </form>

                    {message && <p>{message}</p>}
                </section>

                <section className="legal-panel">
                    <h2>Review Queue</h2>

                    {requests.length === 0 ? (
                        <p>No legal access requests submitted.</p>
                    ) : (
                        <div className="legal-request-list">
                            {requests.map((request) => (
                                <article
                                    key={request.request_id}
                                    className="legal-request-card"
                                >
                                    <div className="legal-request-topline">
                                        <strong>
                                            {request.authority_type.replace("_", " ")}
                                        </strong>
                                        <span className={`request-status ${request.status}`}>
                                            {request.status}
                                        </span>
                                    </div>

                                    <p>
                                        {request.source_type.replace("_", " ")} data for
                                        case {request.case_id ?? "unlinked"}
                                    </p>
                                    <p>{request.requester_organization}</p>
                                    <p>{request.purpose}</p>
                                    <p>{request.scope_description}</p>

                                    <textarea
                                        placeholder="Review notes"
                                        value={reviewNotes[request.request_id] || ""}
                                        onChange={(e) =>
                                            setReviewNotes({
                                                ...reviewNotes,
                                                [request.request_id]: e.target.value,
                                            })
                                        }
                                    />

                                    <div className="legal-actions">
                                        <button
                                            onClick={() =>
                                                reviewRequest(
                                                    request.request_id,
                                                    "approved"
                                                )
                                            }
                                        >
                                            Approve
                                        </button>
                                        <button
                                            onClick={() =>
                                                reviewRequest(request.request_id, "denied")
                                            }
                                        >
                                            Deny
                                        </button>
                                        <button
                                            onClick={() =>
                                                reviewRequest(
                                                    request.request_id,
                                                    "revoked"
                                                )
                                            }
                                        >
                                            Revoke
                                        </button>
                                    </div>
                                </article>
                            ))}
                        </div>
                    )}
                </section>
            </div>
        </div>
    );
}

export default LegalAccessRequests;
