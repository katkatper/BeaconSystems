import React, { useEffect, useMemo, useState } from "react";
import SightingMap from "./SightingMap.jsx";

const sourceTypes = [
    "hospital",
    "transportation",
    "camera",
    "toll",
    "cell_provider",
    "social_media",
    "other",
];

function IntelligenceCenter() {
    const [sightings, setSightings] = useState([]);
    const [externalRecords, setExternalRecords] = useState([]);
    const [integrationSources, setIntegrationSources] = useState([]);
    const [minimumConfidence, setMinimumConfidence] = useState(0);
    const [selectedCaseId, setSelectedCaseId] = useState("all");
    const [selectedSourceType, setSelectedSourceType] = useState("all");
    const [lastUpdated, setLastUpdated] = useState(null);

    useEffect(() => {
        let isMounted = true;
        const token = localStorage.getItem("token");
        const headers = { Authorization: `Bearer ${token}` };

        const loadIntelligence = async () => {
            try {
                const [sightingsResponse, recordsResponse, sourcesResponse] =
                    await Promise.all([
                        fetch("http://127.0.0.1:8000/sightings/", { headers }),
                        fetch("http://127.0.0.1:8000/external-records/", { headers }),
                        fetch("http://127.0.0.1:8000/integrations/", { headers }),
                    ]);

                const [sightingsData, recordsData, sourcesData] = await Promise.all([
                    sightingsResponse.ok ? sightingsResponse.json() : [],
                    recordsResponse.ok ? recordsResponse.json() : [],
                    sourcesResponse.ok ? sourcesResponse.json() : [],
                ]);

                if (!isMounted) return;

                setSightings(Array.isArray(sightingsData) ? sightingsData : []);
                setExternalRecords(Array.isArray(recordsData) ? recordsData : []);
                setIntegrationSources(Array.isArray(sourcesData) ? sourcesData : []);
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

    const filteredSightings = sightings.filter((sighting) => {
        const matchesConfidence =
            (sighting.confidence_score ?? 0) >= minimumConfidence;

        const matchesCase =
            selectedCaseId === "all" || String(sighting.case_id) === selectedCaseId;

        return matchesConfidence && matchesCase;
    });

    const filteredRecords = externalRecords.filter((record) => {
        const matchesCase =
            selectedCaseId === "all" || String(record.case_id) === selectedCaseId;

        const matchesSource =
            selectedSourceType === "all" || record.record_type === selectedSourceType;

        return matchesCase && matchesSource;
    });

    const sourceCounts = useMemo(() => {
        return sourceTypes.reduce((counts, sourceType) => {
            counts[sourceType] = externalRecords.filter(
                (record) => record.record_type === sourceType
            ).length;
            return counts;
        }, {});
    }, [externalRecords]);

    const activeSourceCount = integrationSources.filter(
        (source) => source.is_active
    ).length;

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

            <div className="intelligence-metrics">
                <div>
                    <span>Mapped sightings</span>
                    <strong>{filteredSightings.length}</strong>
                </div>
                <div>
                    <span>External records</span>
                    <strong>{filteredRecords.length}</strong>
                </div>
                <div>
                    <span>Active sources</span>
                    <strong>{activeSourceCount}</strong>
                </div>
            </div>

            <div className="intelligence-controls">
                <label>
                    Confidence
                    <select
                        value={minimumConfidence}
                        onChange={(e) => setMinimumConfidence(Number(e.target.value))}
                    >
                        <option value={0}>All</option>
                        <option value={0.5}>Medium +</option>
                        <option value={0.8}>High only</option>
                    </select>
                </label>

                <label>
                    Case
                    <select
                        value={selectedCaseId}
                        onChange={(e) => setSelectedCaseId(e.target.value)}
                    >
                        <option value="all">All cases</option>
                        {[...new Set(sightings.map((s) => s.case_id))]
                            .filter(Boolean)
                            .map((caseId) => (
                                <option key={caseId} value={caseId}>
                                    Case #{caseId}
                                </option>
                            ))}
                    </select>
                </label>

                <label>
                    Source
                    <select
                        value={selectedSourceType}
                        onChange={(e) => setSelectedSourceType(e.target.value)}
                    >
                        <option value="all">All sources</option>
                        {sourceTypes.map((sourceType) => (
                            <option key={sourceType} value={sourceType}>
                                {sourceType.replace("_", " ")}
                            </option>
                        ))}
                    </select>
                </label>
            </div>

            <div className="source-grid">
                {sourceTypes.map((sourceType) => (
                    <div key={sourceType} className="source-card">
                        <span>{sourceType.replace("_", " ")}</span>
                        <strong>{sourceCounts[sourceType] ?? 0}</strong>
                    </div>
                ))}
            </div>

            <div className="intelligence-layout">
                <section className="intelligence-panel map-panel">
                    <h2>Live Map</h2>
                    <SightingMap sightings={filteredSightings} />
                </section>

                <section className="intelligence-panel">
                    <h2>External Source Feed</h2>
                    {filteredRecords.length === 0 ? (
                        <p>No authorized external records match the current filters.</p>
                    ) : (
                        <div className="feed-list">
                            {filteredRecords.map((record) => (
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
                        </div>
                    )}
                </section>
            </div>
        </div>
    );
}

export default IntelligenceCenter;
