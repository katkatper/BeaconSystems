import React, { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { apiGet, apiPost, apiPostForm } from "../api.jsx";
import ActiveFilterBanner from "../components/ActiveFilterBanner.jsx";
import ShowMoreControls from "../components/ShowMoreControls.jsx";

function MissingPersonsList() {

    const [searchParams, setSearchParams] = useSearchParams();
    const riskFilter = searchParams.get("risk") || "";
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
        primary_address: "",
        housing_status: "unknown",
        school_name: "",
        school_address: "",
        employer_name: "",
        work_address: "",
        employment_status: "",
        photo_url: "",
    });

    const loadPersons = useCallback(() => {
        const params = new URLSearchParams({ limit: "100" });

        if (searchTerm.trim()) {
            params.set("q", searchTerm.trim());
        }

        if (reportDate) {
            params.set("reported_on", reportDate);
        }

        apiGet(`/persons/?${params.toString()}`)
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
            primary_address: "",
            housing_status: "unknown",
            school_name: "",
            school_address: "",
            employer_name: "",
            work_address: "",
            employment_status: "",
            photo_url: "",
        });
        setPhotoFile(null);
        setPhotoInputKey((current) => current + 1);
    };

    const handleManualAdd = async (event) => {
        event.preventDefault();

        try {
            let uploadedPhotoUrl = formData.photo_url;

            if (photoFile) {
                const uploadData = new FormData();
                uploadData.append("file", photoFile);

                const uploadResult = await apiPostForm("/persons/photo-upload", uploadData);
                uploadedPhotoUrl = uploadResult.photo_url;
            }

            const payload = {
                ...formData,
                age: formData.age ? Number(formData.age) : null,
                weight: formData.weight ? Number(formData.weight) : null,
                photo_url: uploadedPhotoUrl,
            };

            const created = await apiPost("/persons/", payload);

            setMessage(`Missing person added and case ${created.case_number || ""} opened.`.trim());
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
    const filteredPersons = persons.filter((person) => {
        const riskLevel = (person.risk_level || "").toLowerCase();

        if (riskFilter === "high") {
            return riskLevel === "high" || riskLevel === "critical";
        }

        if (riskFilter) {
            return riskLevel === riskFilter;
        }

        return true;
    });
    const sortedPersons = [...filteredPersons].sort((firstPerson, secondPerson) =>
        getPersonName(firstPerson).localeCompare(getPersonName(secondPerson))
    );
    const visiblePersons = sortedPersons.slice(0, visiblePersonCount);
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
                        <select name="housing_status" value={formData.housing_status} onChange={handleChange}>
                            <option value="unknown">Housing Status Unknown</option>
                            <option value="housed">Has Address</option>
                            <option value="homeless">Homeless / Unhoused</option>
                            <option value="transient">Transient</option>
                        </select>
                        <input
                            name="primary_address"
                            placeholder="Home address, last known residence, or homeless location"
                            value={formData.primary_address}
                            onChange={handleChange}
                        />
                        <input name="school_name" placeholder="School Name (if student)" value={formData.school_name} onChange={handleChange} />
                        <input name="school_address" placeholder="School Address (if student)" value={formData.school_address} onChange={handleChange} />
                        <input name="employer_name" placeholder="Employer / Retired / Not employed" value={formData.employer_name} onChange={handleChange} />
                        <input name="work_address" placeholder="Work Address (if adult)" value={formData.work_address} onChange={handleChange} />
                        <input name="employment_status" placeholder="Employment status, retired, student, or unknown" value={formData.employment_status} onChange={handleChange} />
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

                    {riskFilter && (
                        <ActiveFilterBanner
                            compact
                            onClear={() => {
                                setSearchParams({});
                                setVisiblePersonCount(2);
                            }}
                        >
                            {riskFilter === "high"
                                ? "Showing high and critical risk subjects"
                                : `Showing ${riskFilter} risk subjects`}
                        </ActiveFilterBanner>
                    )}

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

                        <ShowMoreControls
                            total={sortedPersons.length}
                            visible={visiblePersonCount}
                            noun="persons"
                            onShowMore={() => {
                                setVisiblePersonCount((current) =>
                                    Math.min(current + 4, sortedPersons.length)
                                );
                            }}
                            onShowAll={() => setVisiblePersonCount(sortedPersons.length)}
                            onShowFewer={() => setVisiblePersonCount(2)}
                        />
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
                                    <p>Housing: {selectedPerson.housing_status || "Unknown"}</p>
                                    <p className="full-width-field">Address: {selectedPerson.primary_address || "Not recorded"}</p>
                                    <p className="full-width-field">School: {selectedPerson.school_name || "Not recorded"}</p>
                                    <p className="full-width-field">School Address: {selectedPerson.school_address || "Not recorded"}</p>
                                    <p className="full-width-field">Employer / Status: {selectedPerson.employer_name || selectedPerson.employment_status || "Not recorded"}</p>
                                    <p className="full-width-field">Work Address: {selectedPerson.work_address || "Not recorded"}</p>
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
