import React, { useCallback, useEffect, useState } from "react";

function MissingPersonsList() {

    const [persons, setPersons] = useState([]);
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");
    const [visiblePersonCount, setVisiblePersonCount] = useState(2);
    const [searchTerm, setSearchTerm] = useState("");
    const [reportDate, setReportDate] = useState("");
    const [selectedPersonId, setSelectedPersonId] = useState(null);
    const [photoFile, setPhotoFile] = useState(null);
    const [photoInputKey, setPhotoInputKey] = useState(0);
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
        medical_conditions: "",
        photo_url: "",
    });

    const loadPersons = useCallback(() => {
        const token = localStorage.getItem("token");

        const params = new URLSearchParams({ limit: "100" });

        if (searchTerm.trim()) {
            params.set("q", searchTerm.trim());
        }

        if (reportDate) {
            params.set("reported_on", reportDate);
        }

        fetch(`http://127.0.0.1:8000/persons/?${params.toString()}`, {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        })
            .then((res) => {
                if (!res.ok) {
                    throw new Error("Failed to load persons");
                }

                return res.json();
            })
            .then((data) => {
                setPersons(Array.isArray(data) ? data : []);
                setError("");
            })
            .catch((err) => {
                console.error(err);
                setError("Could not load missing persons.");
            });
    }, [reportDate, searchTerm]);

    useEffect(() => {
        loadPersons();
    }, [loadPersons]);

    useEffect(() => {
        if (!message) return undefined;

        const timeout = setTimeout(() => {
            setMessage("");
        }, 20000);

        return () => clearTimeout(timeout);
    }, [message]);

    const handleChange = (event) => {
        setFormData((current) => ({
            ...current,
            [event.target.name]: event.target.value,
        }));
    };

    const resetForm = () => {
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
            medical_conditions: "",
            photo_url: "",
        });
        setPhotoFile(null);
        setPhotoInputKey((current) => current + 1);
    };

    const handleManualAdd = async (event) => {
        event.preventDefault();

        const token = localStorage.getItem("token");

        try {
            let uploadedPhotoUrl = formData.photo_url;

            if (photoFile) {
                const uploadData = new FormData();
                uploadData.append("file", photoFile);

                const uploadResponse = await fetch("http://127.0.0.1:8000/persons/photo-upload", {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                    body: uploadData,
                });

                if (!uploadResponse.ok) {
                    const errorData = await uploadResponse.json().catch(() => ({}));
                    throw new Error(errorData.detail || "Could not upload missing person photo");
                }

                const uploadResult = await uploadResponse.json();
                uploadedPhotoUrl = uploadResult.photo_url;
            }

            const payload = {
                ...formData,
                age: formData.age ? Number(formData.age) : null,
                weight: formData.weight ? Number(formData.weight) : null,
                photo_url: uploadedPhotoUrl,
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
                throw new Error("Failed to add missing person");
            }

            setMessage("Missing person added to the registry.");
            resetForm();
            setVisiblePersonCount(6);
            await loadPersons();
        } catch (err) {
            console.error(err);
            setMessage(err.message || "Could not add missing person.");
        }
    };

    const formatReportDate = (dateValue) => {
        if (!dateValue) return "Not recorded";

        return new Date(dateValue).toLocaleDateString();
    };
    const getPersonName = (person) => `${person.first_name || ""} ${person.last_name || ""}`.trim();
    const sortedPersons = [...persons].sort((firstPerson, secondPerson) =>
        getPersonName(firstPerson).localeCompare(getPersonName(secondPerson))
    );
    const visiblePersons = sortedPersons.slice(0, visiblePersonCount);
    const remainingPersonCount = Math.max(sortedPersons.length - visiblePersonCount, 0);
    const selectedPerson = sortedPersons.find((person) => person.person_id === selectedPersonId) || visiblePersons[0];

    return (

        <div className="missing-persons-page">
            <div className="missing-persons-header">
                <h1>Missing Persons</h1>
            </div>

            {error && <p className="alert-banner">{error}</p>}
            {message && (
                <p className="alert-banner">
                    {message}
                </p>
            )}

            <section className="missing-persons-command-grid">
                <form className="missing-person-card missing-person-intake-card" onSubmit={handleManualAdd}>
                    <div className="dashboard-panel-header">
                        <span>Manual Add</span>
                        <strong>New person</strong>
                    </div>
                    <div className="missing-person-form-grid">
                        <input required name="first_name" placeholder="First Name" value={formData.first_name} onChange={handleChange} />
                        <input required name="last_name" placeholder="Last Name" value={formData.last_name} onChange={handleChange} />
                        <input name="age" placeholder="Age" value={formData.age} onChange={handleChange} />
                        <input name="last_seen_location" placeholder="Last Seen Location" value={formData.last_seen_location} onChange={handleChange} />
                        <input name="eye_color" placeholder="Eye Color" value={formData.eye_color} onChange={handleChange} />
                        <input name="hair_color" placeholder="Hair Color" value={formData.hair_color} onChange={handleChange} />
                        <input name="height" placeholder="Height" value={formData.height} onChange={handleChange} />
                        <input name="weight" placeholder="Weight" value={formData.weight} onChange={handleChange} />
                        <label className="missing-person-photo-upload full-width-field">
                            <span>Upload Photo</span>
                            <input
                                key={photoInputKey}
                                type="file"
                                accept="image/png,image/jpeg,image/webp,image/gif"
                                onChange={(event) => {
                                    setPhotoFile(event.target.files?.[0] || null);
                                }}
                            />
                            <small>{photoFile ? photoFile.name : "No photo selected"}</small>
                        </label>
                        <select name="risk_level" value={formData.risk_level} onChange={handleChange}>
                            <option value="low">Low Risk</option>
                            <option value="medium">Medium Risk</option>
                            <option value="high">High Risk</option>
                            <option value="critical">Critical Risk</option>
                        </select>
                        <select name="status" value={formData.status} onChange={handleChange}>
                            <option value="missing">Missing</option>
                            <option value="found">Found</option>
                            <option value="unknown">Unknown</option>
                        </select>
                        <textarea
                            className="full-width-field"
                            name="medical_conditions"
                            placeholder="Medical needs, disability, medication dependency, or cognitive concerns"
                            value={formData.medical_conditions}
                            onChange={handleChange}
                        />
                        <textarea
                            className="full-width-field"
                            name="description"
                            placeholder="Description, circumstances, medical needs, or known risk factors"
                            value={formData.description}
                            onChange={handleChange}
                        />
                    </div>
                    <button type="submit">Add Missing Person</button>
                </form>

                <section className="missing-person-card missing-registry-panel">
                    <div className="dashboard-panel-header">
                        <span>Registry</span>
                    </div>

                    <div className="missing-person-search-row">
                        <input
                            type="search"
                            placeholder="Search by name, location, status, risk, or description"
                            value={searchTerm}
                            onChange={(event) => {
                                setSearchTerm(event.target.value);
                                setVisiblePersonCount(2);
                            }}
                        />
                        <label className="report-date-search">
                            <span>Report Date</span>
                            <input
                                type="date"
                                value={reportDate}
                                aria-label="Search by report date"
                                onChange={(event) => {
                                    setReportDate(event.target.value);
                                    setVisiblePersonCount(2);
                                }}
                            />
                        </label>
                        {(searchTerm || reportDate) && (
                            <button
                                type="button"
                                className="list-toggle-button"
                                onClick={() => {
                                    setSearchTerm("");
                                    setReportDate("");
                                    setVisiblePersonCount(2);
                                }}
                            >
                                Clear
                            </button>
                        )}
                    </div>

                    {sortedPersons.length === 0 && !error && (
                        <p>No missing persons found.</p>
                    )}

                    <div className="missing-persons-grid">
                        {visiblePersons.map((person) => (
                            <button
                                key={person.person_id}
                                type="button"
                                className={`missing-person-name-row ${
                                    selectedPerson?.person_id === person.person_id ? "active" : ""
                                }`}
                                onClick={() => setSelectedPersonId(person.person_id)}
                            >
                                <span>{getPersonName(person)}</span>
                            </button>
                        ))}

                        {sortedPersons.length > 2 && (
                            <div className="list-toggle-row">
                                {remainingPersonCount > 0 ? (
                                    <>
                                        <button
                                            type="button"
                                            className="list-toggle-button"
                                            onClick={() => {
                                                setVisiblePersonCount((current) =>
                                                    Math.min(current + 4, sortedPersons.length)
                                                );
                                            }}
                                        >
                                            Show {Math.min(4, remainingPersonCount)} more persons
                                        </button>
                                        <button
                                            type="button"
                                            className="list-toggle-button"
                                            onClick={() => setVisiblePersonCount(sortedPersons.length)}
                                        >
                                            Show all
                                        </button>
                                    </>
                                ) : (
                                    <button
                                        type="button"
                                        className="list-toggle-button"
                                        onClick={() => setVisiblePersonCount(2)}
                                    >
                                        Show fewer
                                    </button>
                                )}
                            </div>
                        )}
                    </div>

                    {selectedPerson && (
                        <article className="missing-person-selected-detail">
                            <div className="dashboard-panel-header">
                                <span>Selected Person</span>
                                <strong>{getPersonName(selectedPerson)}</strong>
                            </div>
                            <div className="missing-person-selected-layout">
                                <div className="missing-person-selected-photo">
                                    {selectedPerson.photo_url ? (
                                        <img src={selectedPerson.photo_url} alt={`${getPersonName(selectedPerson)} profile`} />
                                    ) : (
                                        <span>No photo</span>
                                    )}
                                </div>
                                <div className="missing-person-detail-grid">
                                    <p>Age: {selectedPerson.age || "Unknown"}</p>
                                    <p>Report Date: {formatReportDate(selectedPerson.created_at)}</p>
                                    <p>Status: {selectedPerson.status || "Unknown"}</p>
                                    <p>Risk Level: {selectedPerson.risk_level || "Unknown"}</p>
                                    <p className="full-width-field">Medical Needs: {selectedPerson.medical_conditions || "Not recorded"}</p>
                                    <p className="full-width-field">Last Seen: {selectedPerson.last_seen_location || "Not recorded"}</p>
                                    <p className="full-width-field">{selectedPerson.description || "No description recorded."}</p>
                                </div>
                            </div>
                            <button
                                type="button"
                                onClick={() => {
                                    window.location.href = `/persons/${selectedPerson.person_id}`;
                                }}
                            >
                                View Profile
                            </button>
                        </article>
                    )}
                </section>
            </section>
        </div>
    );
}

export default MissingPersonsList;
