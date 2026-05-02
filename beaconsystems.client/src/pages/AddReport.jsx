import React, { useState } from "react";

function AddPerson() {
    const [formData, setFormData] = useState({
        first_name: "",
        last_name: "",
        age: "",
        eye_color: "",
        hair_color: "",
        height: "",
        weight: "",
        last_seen_location: "",
        risk_level: "high",
        status: "missing",
        description: "",
    });

    const [message, setMessage] = useState("");

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
                age: formData.age ? Number(formData.age) : null,
                weight: formData.weight ? Number(formData.weight) : null,
            };

            const response = await fetch("http://127.0.0.1:8000/persons/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                throw new Error("Failed to create person");
            }

            const data = await response.json();
            console.log("Person created:", data);

            setMessage("Missing person created successfully.");

            setFormData({
                first_name: "",
                last_name: "",
                age: "",
                eye_color: "",
                hair_color: "",
                height: "",
                weight: "",
                last_seen_location: "",
                risk_level: "high",
                status: "missing",
                description: "",
            });
        } catch (err) {
            console.error(err);
            setMessage("Could not create missing person.");
        }
    };

    return (
        <div>
            <h1>Report Missing Person</h1>

            <form onSubmit={handleSubmit}>
                <input name="first_name" placeholder="First Name" value={formData.first_name} onChange={handleChange} />
                <input name="last_name" placeholder="Last Name" value={formData.last_name} onChange={handleChange} />
                <input name="age" placeholder="Age" value={formData.age} onChange={handleChange} />
                <input name="eye_color" placeholder="Eye Color" value={formData.eye_color} onChange={handleChange} />
                <input name="hair_color" placeholder="Hair Color" value={formData.hair_color} onChange={handleChange} />
                <input name="height" placeholder="Height" value={formData.height} onChange={handleChange} />
                <input name="weight" placeholder="Weight" value={formData.weight} onChange={handleChange} />
                <input name="last_seen_location" placeholder="Last Seen Location" value={formData.last_seen_location} onChange={handleChange} />

                <select name="risk_level" value={formData.risk_level} onChange={handleChange}>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                </select>

                <select name="status" value={formData.status} onChange={handleChange}>
                    <option value="missing">Missing</option>
                    <option value="found">Found</option>
                    <option value="unknown">Unknown</option>
                </select>

                <textarea name="description" placeholder="Description" value={formData.description} onChange={handleChange} />

                <button type="submit">Submit Missing Person</button>
            </form>

            {message && <p>{message}</p>}
        </div>
    );
}

export default AddPerson;