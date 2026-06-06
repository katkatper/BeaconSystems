import React, { useEffect, useState } from "react";
import IntelligenceMap3D from "./IntelligenceMap3D.jsx";

function IntelligenceCenter() {
    const [sightings, setSightings] = useState([]);
    const [externalRecords, setExternalRecords] = useState([]);
    const [visibleRecordCount, setVisibleRecordCount] = useState(2);
    const [lastUpdated, setLastUpdated] = useState(null);

    useEffect(() => {
        let isMounted = true;
        const token = localStorage.getItem("token");
        const headers = { Authorization: `Bearer ${token}` };

        const loadIntelligence = async () => {
            try {
                const [sightingsResponse, recordsResponse] =
                    await Promise.all([
                        fetch("http://127.0.0.1:8000/sightings/", { headers }),
                        fetch("http://127.0.0.1:8000/external-records/", { headers }),
                    ]);

                const [sightingsData, recordsData] = await Promise.all([
                    sightingsResponse.ok ? sightingsResponse.json() : [],
                    recordsResponse.ok ? recordsResponse.json() : [],
                ]);

                if (!isMounted) return;

                setSightings(Array.isArray(sightingsData) ? sightingsData : []);
                setExternalRecords(Array.isArray(recordsData) ? recordsData : []);
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

    return (
        <div className="intelligence-page">
            <div className="intelligence-header">
                <div>
                    <h1>Beacon Intelligence Center</h1>
                    <p>
                        Authorized source fusion for missing-person and trafficking
                        investigations.
                    </p>
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
