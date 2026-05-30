import React, { useEffect, useState } from "react";

const orderTypes = [
    "subpoena",
    "court_order",
    "search_warrant",
    "wiretap_order",
    "national_security_letter",
];

const partnerTypes = [
    "transportation",
    "communications",
    "camera",
    "toll",
    "cell_provider",
    "social_media",
    "coroner",
    "genealogy",
    "missing_persons_organization",
    "hospital",
    "other",
];

function LegalOrders() {
    const [orders, setOrders] = useState([]);
    const [message, setMessage] = useState("");
    const [form, setForm] = useState({
        case_id: "",
        requester_name: "",
        requester_organization: "",
        requester_role: "district_attorney",
        contact_email: "",
        authority_type: "subpoena",
        source_type: "communications",
        target_identifier: "",
        jurisdiction: "",
        legal_reference: "",
        purpose: "",
        scope_description: "",
        minimization_plan: "",
        retention_plan: "",
        document_location: "",
    });

    const token = localStorage.getItem("token");
    const pendingOrders = orders.filter((order) => order.status !== "approved");
    const approvedOrders = orders.filter((order) => order.status === "approved");

    const loadOrders = async () => {
        const response = await fetch("http://127.0.0.1:8000/legal-access/", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            throw new Error("Could not load legal orders");
        }

        const data = await response.json();
        setOrders(
            Array.isArray(data)
                ? data.filter((item) => orderTypes.includes(item.authority_type))
                : []
        );
    };

    useEffect(() => {
        loadOrders().catch((err) => {
            console.error(err);
            setMessage("Could not load legal orders.");
        });
    }, []);

    const handleChange = (event) => {
        setForm((current) => ({
            ...current,
            [event.target.name]: event.target.value,
        }));
    };

    const submitOrder = async (event) => {
        event.preventDefault();
        setMessage("");

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
                throw new Error("Could not create legal order");
            }

            setMessage("Legal order request submitted to DA or court workflow.");
            setForm((current) => ({
                ...current,
                target_identifier: "",
                legal_reference: "",
                purpose: "",
                scope_description: "",
                minimization_plan: "",
                retention_plan: "",
                document_location: "",
            }));
            await loadOrders();
        } catch (err) {
            console.error(err);
            setMessage("Could not create legal order package.");
        }
    };

    return (
        <div className="legal-access-page">
            <div className="legal-access-header">
                <h1>Legal Orders</h1>
                <p>
                    Request subpoenas, court orders, warrants, wiretap orders, and
                    national security letters from the DA or court, then track approved
                    documents for partner service.
                </p>
            </div>

            {message && <p className="alert-banner">{message}</p>}

            <div className="legal-access-layout">
                <section className="legal-panel">
                    <h2>Request Legal Order</h2>

                    <form className="legal-form" onSubmit={submitOrder}>
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
                            placeholder="DA office, court, or requesting agency"
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
                            {orderTypes.map((type) => (
                                <option key={type} value={type}>
                                    {type.replaceAll("_", " ")}
                                </option>
                            ))}
                        </select>

                        <select
                            name="source_type"
                            value={form.source_type}
                            onChange={handleChange}
                        >
                            {partnerTypes.map((type) => (
                                <option key={type} value={type}>
                                    {type.replaceAll("_", " ")}
                                </option>
                            ))}
                        </select>

                        <input
                            name="target_identifier"
                            placeholder="Subject, account, device, plate, route, or location"
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
                            placeholder="Subpoena, warrant, order, or docket number"
                            value={form.legal_reference}
                            onChange={handleChange}
                        />
                        <input
                            name="document_location"
                            placeholder="Secure document path or evidence reference"
                            value={form.document_location}
                            onChange={handleChange}
                        />

                        <textarea
                            name="purpose"
                            placeholder="Purpose for requesting this legal document"
                            value={form.purpose}
                            onChange={handleChange}
                            required
                        />
                        <textarea
                            name="scope_description"
                            placeholder="Requested partner, date range, data fields, legal limits, and court/DA instructions"
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

                        <button type="submit">Request Legal Order</button>
                    </form>
                </section>

                <section className="legal-panel">
                    <h2>Legal Order Requests</h2>

                    {pendingOrders.length === 0 ? (
                        <p>No legal order requests awaiting approval.</p>
                    ) : (
                        <div className="legal-request-list">
                            {pendingOrders.map((order) => (
                                <article
                                    key={order.request_id}
                                    className="legal-request-card"
                                >
                                    <div className="legal-request-topline">
                                        <strong>
                                            {order.authority_type.replaceAll("_", " ")}
                                        </strong>
                                        <span className={`request-status ${order.status}`}>
                                            {order.status}
                                        </span>
                                    </div>
                                    <p>
                                        {order.source_type.replaceAll("_", " ")} partner
                                        request for case {order.case_id ?? "unlinked"}
                                    </p>
                                    <p>{order.target_identifier || "No target listed"}</p>
                                    <p>{order.legal_reference || "No legal reference listed"}</p>
                                    <p>{order.scope_description}</p>
                                </article>
                            ))}
                        </div>
                    )}
                </section>

                <section className="legal-panel">
                    <h2>Approved Legal Orders</h2>

                    {approvedOrders.length === 0 ? (
                        <p>No approved legal orders ready for partner service.</p>
                    ) : (
                        <div className="legal-request-list">
                            {approvedOrders.map((order) => (
                                <article
                                    key={order.request_id}
                                    className="legal-request-card"
                                >
                                    <div className="legal-request-topline">
                                        <strong>
                                            {order.authority_type.replaceAll("_", " ")}
                                        </strong>
                                        <span className={`request-status ${order.status}`}>
                                            Ready for partner
                                        </span>
                                    </div>
                                    <p>
                                        Send to {order.source_type.replaceAll("_", " ")} partner
                                        for case {order.case_id ?? "unlinked"}
                                    </p>
                                    <p>{order.target_identifier || "No target listed"}</p>
                                    <p>{order.legal_reference || "No legal reference listed"}</p>
                                    <p>{order.document_location || "No secure document path listed"}</p>
                                    <p>{order.scope_description}</p>
                                </article>
                            ))}
                        </div>
                    )}
                </section>
            </div>
        </div>
    );
}

export default LegalOrders;
