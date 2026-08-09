import { apiUrl } from "../api.jsx";
import React, { useState } from "react";

function AddExternalRecord() {
    const [form, setForm] = useState({
        integration_source_id: 1,
        record_type: "hospital",
        first_name: "",
        last_name: "",
        age: "",
        location: "",
        notes: "",
    });

    const [message, setMessage] = useState("");

    function handleChange(e) {
        setForm({
            ...form,
            [e.target.name]: e.target.value,
        });
    }

    async function handleSubmit(e) {
        e.preventDefault();

        const params = new URLSearchParams({
            integration_source_id: form.integration_source_id,
            record_type: form.record_type,
            first_name: form.first_name,
            last_name: form.last_name,
            age: form.age,
            location: form.location,
            notes: form.notes,
        });

        const response = await fetch(
            apiUrl(`/external-records/?${params.toString()}`),
            {
                method: "POST",
            }
        );

        if (response.ok) {
            setMessage("External record added successfully.");
            setForm({
                integration_source_id: 1,
                record_type: "hospital",
                first_name: "",
                last_name: "",
                age: "",
                location: "",
                notes: "",
            });
        } else {
            setMessage("Failed to add external record.");
        }
    }

    return (
        <div>
            <h2>Add External Record</h2>

            <form onSubmit={handleSubmit}>
                <input name="record_type" value={form.record_type} onChange={handleChange} placeholder="Record Type" />
                <input name="first_name" value={form.first_name} onChange={handleChange} placeholder="First Name" />
                <input name="last_name" value={form.last_name} onChange={handleChange} placeholder="Last Name" />
                <input name="age" value={form.age} onChange={handleChange} placeholder="Age" />
                <input name="location" value={form.location} onChange={handleChange} placeholder="Location" />
                <textarea name="notes" value={form.notes} onChange={handleChange} placeholder="Notes" />

                <button type="submit">Submit External Record</button>
            </form>

            <p>{message}</p>
        </div>
    );
}

export default AddExternalRecord;