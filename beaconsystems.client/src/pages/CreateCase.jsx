import React, { useEffect, useState } from "react";

function CreateCase() {
    const [persons, setPersons] = useState([]);
    const [message, setMessage] = useState("");

    const [formData, setFormData] = useState({
        case_number: "",
        person_id: "",
        last_seen_location: "",
        priority_level: "high",
        case_status: "open",
        notes: "",
        investigator_id: "1",
        agency_id: "305",
    });

    useEffect(() => {
        const token = localStorage.getItem("token");

        fetch("http://127.0.0.1:8000/persons/", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        })
            .then((res) => res.json())
            .then((data) => setPersons(data))
            .catch((err) => {
                console.error(err);
                setMessage("Could not load persons.");
            });
    }, []);

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value,
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        const token = localStorage.getItem("token");

        try {
            const payload = {
                ...formData,
                person_id: Number(formData.person_id),
                investigator_id: Number(formData.investigator_id),
                agency_id: Number(formData.agency_id),
            };

            const response = await fetch("http://127.0.0.1:8000/cases/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                throw new Error("Failed to create case");
            }

            const data = await response.json();
            console.log("Case created:", data);

            setMessage("Case created successfully.");
        } catch (err) {
            console.error(err);
            setMessage("Could not create case.");
        }
    };

    return (
        <div>
            <h1>Create Case</h1>

            <form onSubmit={handleSubmit}>
                <input
                    name="case_number"
                    placeholder="Case Number"
                    value={formData.case_number}
                    onChange={handleChange}
                />

                <select
                    name="person_id"
                    value={formData.person_id}
                    onChange={handleChange}
                >
                    <option value="">Select Missing Person</option>

                    {persons.map((person) => (
                        <option
                            key={person.person_id}
                            value={person.person_id}
                        >
                            {person.first_name} {person.last_name}
                        </option>
                    ))}
                </select>

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
                    <option value="critical">Critical</option>
                </select>

                <select
                    name="case_status"
                    value={formData.case_status}
                    onChange={handleChange}
                >
                    <option value="open">Open</option>
                    <option value="investigating">Investigating</option>
                    <option value="closed">Closed</option>
                </select>

                <textarea
                    name="notes"
                    placeholder="Notes"
                    value={formData.notes}
                    onChange={handleChange}
                />

                <input
                    name="investigator_id"
                    placeholder="Investigator ID"
                    value={formData.investigator_id}
                    onChange={handleChange}
                />

                <input
                    name="agency_id"
                    placeholder="Agency ID"
                    value={formData.agency_id}
                    onChange={handleChange}
                />

                <button type="submit">Create Case</button>
            </form>

            {message && <p>{message}</p>}
        </div>
    );
}

export default CreateCase;