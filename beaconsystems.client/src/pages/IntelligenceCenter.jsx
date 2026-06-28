import React, { useEffect, useState } from "react";
import IntelligenceMap3D from "./IntelligenceMap3D.jsx";

function IntelligenceCenter() {
    const [sightings, setSightings] = useState([]);
    const [externalRecords, setExternalRecords] = useState([]);
    const [evidence, setEvidence] = useState([]);
    const [persons, setPersons] = useState([]);
    const [visibleRecordCount, setVisibleRecordCount] = useState(2);
    const [lastUpdated, setLastUpdated] = useState(null);

    useEffect(() => {
        let isMounted = true;
        const token = localStorage.getItem("token");
        const headers = { Authorization: `Bearer ${token}` };

        const loadIntelligence = async () => {
            try {
                const [sightingsResponse, recordsResponse, evidenceResponse, personsResponse] =
                    await Promise.all([
                        fetch("http://127.0.0.1:8000/sightings/", { headers }),
                        fetch("http://127.0.0.1:8000/external-records/", { headers }),
                        fetch("http://127.0.0.1:8000/evidence/", { headers }),
                        fetch("http://127.0.0.1:8000/persons/?limit=100", { headers }),
                    ]);

                const [sightingsData, recordsData, evidenceData, personsData] = await Promise.all([
                    sightingsResponse.ok ? sightingsResponse.json() : [],
                    recordsResponse.ok ? recordsResponse.json() : [],
                    evidenceResponse.ok ? evidenceResponse.json() : [],
                    personsResponse.ok ? personsResponse.json() : [],
                ]);

                if (!isMounted) return;

                setSightings(Array.isArray(sightingsData) ? sightingsData : []);
                setExternalRecords(Array.isArray(recordsData) ? recordsData : []);
                setEvidence(Array.isArray(evidenceData) ? evidenceData : []);
                setPersons(Array.isArray(personsData) ? personsData : []);
                setLastUpdated(new Date());
            } catch (err) {
                console.error(err);
            }
        };

        loadIntelligence();
        const interval = setInterval(loadIntelligence, 10000);

        return () => {
            isMounted = false;
            clearInterval(interval);
        };
    }, []);

    const hasMapCoordinates = (latitude, longitude) =>
        Number.isFinite(Number(latitude)) && Number.isFinite(Number(longitude));

    const mappedLocations = [
        ...evidence
            .filter((item) => hasMapCoordinates(item.evidence_latitude, item.evidence_longitude))
            .map((item) => ({
                id: `evidence-${item.evidence_id}`,
                type: "evidence",
                label: item.evidence_type || "Evidence",
                address: item.evidence_location,
                detail: item.description || item.custody_status || "Evidence location",
                caseId: item.case_id,
                latitude: item.evidence_latitude,
                longitude: item.evidence_longitude,
                confidence: 0.72,
            })),
        ...persons.flatMap((person) => {
            const personName = `${person.first_name || ""} ${person.last_name || ""}`.trim() || "Missing person";
            return [
                hasMapCoordinates(person.primary_address_latitude, person.primary_address_longitude)
                    ? {
                        id: `person-${person.person_id}-primary`,
                        type: "address",
                        label: `${personName} primary address`,
                        address: person.primary_address,
                        detail: "Missing person address",
                        caseId: person.case_id,
                        latitude: person.primary_address_latitude,
                        longitude: person.primary_address_longitude,
                        confidence: 0.64,
                    }
                    : null,
                hasMapCoordinates(person.last_seen_latitude, person.last_seen_longitude)
                    ? {
                        id: `person-${person.person_id}-last-seen`,
                        type: "last_seen",
                        label: `${personName} last seen`,
                        address: person.last_seen_location,
                        detail: "Last seen location",
                        caseId: person.case_id,
                        latitude: person.last_seen_latitude,
                        longitude: person.last_seen_longitude,
                        confidence: 0.82,
                    }
                    : null,
                hasMapCoordinates(person.school_address_latitude, person.school_address_longitude)
                    ? {
                        id: `person-${person.person_id}-school`,
                        type: "school",
                        label: person.school_name || `${personName} school`,
                        address: person.school_address,
                        detail: "School address",
                        caseId: person.case_id,
                        latitude: person.school_address_latitude,
                        longitude: person.school_address_longitude,
                        confidence: 0.58,
                    }
                    : null,
                hasMapCoordinates(person.work_address_latitude, person.work_address_longitude)
                    ? {
                        id: `person-${person.person_id}-work`,
                        type: "work",
                        label: person.employer_name || `${personName} work`,
                        address: person.work_address,
                        detail: "Work address",
                        caseId: person.case_id,
                        latitude: person.work_address_latitude,
                        longitude: person.work_address_longitude,
                        confidence: 0.58,
                    }
                    : null,
            ].filter(Boolean);
        }),
    ];

    return (
        <div className="intelligence-page">
            <div className="intelligence-header">
                <div>
                    <h1>Beacon Intelligence Center</h1>
                </div>

                <div className="live-status">
                    <span className="live-dot" />
                    Live refresh
                    {lastUpdated && (
                        <small>
                            Updated {lastUpdated.toLocaleTimeString()}
                        </small>
                    )}
                </div>
            </div>

            <div className="intelligence-layout">
                <section className="intelligence-map-section">
                    <h2>Live 3D Intelligence Map</h2>
                    <IntelligenceMap3D
                        sightings={sightings}
                        records={externalRecords}
                        mappedLocations={mappedLocations}
                    />
                </section>

                <section className="intelligence-panel">
                    <h2>External Source Feed</h2>
                    {externalRecords.length === 0 ? (
                        <p>No authorized external records available.</p>
                    ) : (
                        <div className="feed-list">
                            {externalRecords.slice(0, visibleRecordCount).map((record) => (
                                <article key={record.id} className="feed-item">
                                    <div>
                                        <strong>{record.record_type}</strong>
                                        <span>
                                            Case {record.case_id ?? "unlinked"} | Person{" "}
                                            {record.person_id ?? "unlinked"}
                                        </span>
                                    </div>
                                    <p>{record.location || "No location provided"}</p>
                                    <p>{record.notes || "No notes provided"}</p>
                                </article>
                            ))}
                            {externalRecords.length > 2 && (
                                <div className="list-toggle-row">
                                    {visibleRecordCount > 2 && (
                                        <button
                                            type="button"
                                            className="list-toggle-button"
                                            onClick={() => setVisibleRecordCount(2)}
                                        >
                                            Show fewer
                                        </button>
                                    )}
                                    {visibleRecordCount < externalRecords.length && (
                                        <>
                                            <button
                                                type="button"
                                                className="list-toggle-button"
                                                onClick={() =>
                                                    setVisibleRecordCount((current) =>
                                                        Math.min(current + 4, externalRecords.length)
                                                    )
                                                }
                                            >
                                                Show {Math.min(4, externalRecords.length - visibleRecordCount)} more records
                                            </button>
                                            <button
                                                type="button"
                                                className="list-toggle-button"
                                                onClick={() => setVisibleRecordCount(externalRecords.length)}
                                            >
                                                Show all
                                            </button>
                                        </>
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </section>
            </div>
        </div>
    );
}

export default IntelligenceCenter;
