import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

function AddPerson() {
    const navigate = useNavigate();

    const [formData, setFormData] = useState({
        case_number: "",
        person_id: "",
        description: "",
        investigator_id: "",
        reporting_agency_id: "",
        last_seen_location: "",
        priority_level: "medium",
        notes: "",
        case_status: "open",
    });

    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value,
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        setError("");
        setSuccess("");

        const token = localStorage.getItem("token");

        if (!token) {
            setError("You must be logged in to create a case.");
            return;
        }

        try {
            const payload = {
                ...formData,
                person_id: Number(formData.person_id),
                investigator_id: formData.investigator_id
                    ? Number(formData.investigator_id)
                    : null,
                reporting_agency_id: formData.reporting_agency_id
                    ? Number(formData.reporting_agency_id)
                    : null,
            };

            const response = await fetch(
                "http://127.0.0.1:8000/cases/",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify(payload),
                }
            );

            if (!response.ok) {
                throw new Error("Failed to create case");
            }

            const data = await response.json();

            console.log("Created case:", data);

            setSuccess("Case created successfully.");

            setTimeout(() => {
                navigate("/");
            }, 1000);

        } catch (err) {
            console.error(err);
            setError("Could not create case.");
        }
    };

    return (
        <div>
            <h1>Report Missing Person</h1>

            <form onSubmit={handleSubmit}>

                <input
                    name="case_number"
                    placeholder="Case Number"
                    value={formData.case_number}
                    onChange={handleChange}
                />

                <input
                    name="person_id"
                    placeholder="Person ID"
                    value={formData.person_id}
                    onChange={handleChange}
                />

                <input
                    name="description"
                    placeholder="Description"
                    value={formData.description}
                    onChange={handleChange}
                />

                <input
                    name="investigator_id"
                    placeholder="Investigator ID"
                    value={formData.investigator_id}
                    onChange={handleChange}
                />

                <input
                    name="reporting_agency_id"
                    placeholder="Reporting Agency ID"
                    value={formData.reporting_agency_id}
                    onChange={handleChange}
                />

                <input
                    name="last_seen_location"
                    placeholder="Last Seen Location"
                    value={formData.last_seen_location}
                    onChange={handleChange}
                />

                <select
                    name="priority_level"
                    value={formData.priority_level}
                    onChange={handleChange}
                >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                </select>

                <textarea
                    name="notes"
                    placeholder="Notes"
                    value={formData.notes}
                    onChange={handleChange}
                />

                <select
                    name="case_status"
                    value={formData.case_status}
                    onChange={handleChange}
                >
                    <option value="open">Open</option>
                    <option value="investigating">Investigating</option>
                    <option value="closed">Closed</option>
                </select>

                <br />
                <br />

                <button type="submit">
                    Submit Report
                </button>

            </form>

            {error && <p>{error}</p>}
            {success && <p>{success}</p>}

        </div>
    );
}

export default AddPerson;