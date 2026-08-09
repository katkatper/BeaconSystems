import { apiUrl } from "../api.jsx";
import React, { lazy, Suspense, useEffect, useState } from "react";

const IntelligenceMap3D = lazy(() => import("./IntelligenceMap3D.jsx"));

const includesAny = (value, terms) => {
    const normalized = String(value || "").toLowerCase();
    return terms.some((term) => normalized.includes(term));
};

const classifyExternalRecord = (record) => {
    const text = `${record.record_type || ""} ${record.notes || ""} ${record.location || ""}`;
    if (includesAny(text, ["traffick", "commercial sex", "forced labor"])) return "human_trafficking";
    if (includesAny(text, ["unidentified remains", "unidentified decedent", "morgue", "coroner", "medical examiner"])) return "unidentified_remains";
    if (includesAny(text, ["child exploitation", "child sexual", "csam", "minor exploitation"])) return "child_exploitation";
    if (includesAny(text, ["license plate", "lpr", "alpr", "plate hit"])) return "lpr_hits";
    if (includesAny(text, ["camera", "surveillance", "ring footage", "video hit"])) return "camera_hits";
    if (includesAny(text, ["social media", "facebook", "instagram", "snapchat", "tiktok"])) return "social_media";
    if (includesAny(text, ["gang", "crew territory"])) return "gang_territories";
    return "crime_clusters";
};

function IntelligenceCenter() {
    const [sightings, setSightings] = useState([]);
    const [externalRecords, setExternalRecords] = useState([]);
    const [bolos, setBolos] = useState([]);
    const [evidence, setEvidence] = useState([]);
    const [persons, setPersons] = useState([]);
    const [lastUpdated, setLastUpdated] = useState(null);
    const [showAiReview, setShowAiReview] = useState(false);

    useEffect(() => {
        let isMounted = true;
        const token = localStorage.getItem("token");
        const headers = { Authorization: `Bearer ${token}` };

        const loadIntelligence = async () => {
            try {
                const [sightingsResponse, recordsResponse, bolosResponse, evidenceResponse, personsResponse] =
                    await Promise.all([
                        fetch(apiUrl("/sightings/"), { headers }),
                        fetch(apiUrl("/external-records/"), { headers }),
                        fetch(apiUrl("/bolos/"), { headers }),
                        fetch(apiUrl("/evidence/"), { headers }),
                        fetch(apiUrl("/persons/?limit=100"), { headers }),
                    ]);

                const [sightingsData, recordsData, bolosData, evidenceData, personsData] = await Promise.all([
                    sightingsResponse.ok ? sightingsResponse.json() : [],
                    recordsResponse.ok ? recordsResponse.json() : [],
                    bolosResponse.ok ? bolosResponse.json() : [],
                    evidenceResponse.ok ? evidenceResponse.json() : [],
                    personsResponse.ok ? personsResponse.json() : [],
                ]);

                if (!isMounted) return;

                setSightings(Array.isArray(sightingsData) ? sightingsData : []);
                setExternalRecords(Array.isArray(recordsData) ? recordsData : []);
                setBolos(Array.isArray(bolosData) ? bolosData : []);
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
        latitude !== null && latitude !== undefined && latitude !== "" &&
        longitude !== null && longitude !== undefined && longitude !== "" &&
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
                analysisLayer: includesAny(`${item.evidence_type} ${item.description}`, ["unidentified remains", "human remains", "decedent"])
                    ? "unidentified_remains"
                    : "crime_clusters",
            })),
        ...bolos
            .filter((bolo) => hasMapCoordinates(bolo.latitude, bolo.longitude))
            .map((bolo) => ({
                id: `bolo-${bolo.bolo_id}`,
                type: "bolo",
                label: bolo.title || "BOLO",
                address: bolo.geocoded_address || bolo.last_known_location,
                detail: bolo.description || "Active BOLO alert",
                caseId: bolo.case_id,
                latitude: bolo.latitude,
                longitude: bolo.longitude,
                confidence: bolo.geocode_score
                    ? Math.max(0.35, Math.min(Number(bolo.geocode_score) / 100, 0.95))
                    : 0.74,
                analysisLayer: includesAny(`${bolo.title} ${bolo.description}`, ["gang"])
                    ? "gang_territories"
                    : "crime_clusters",
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
                        analysisLayer: Number(person.criminal_arrests_count || 0) >= 2
                            ? "repeat_offenders"
                            : Number(person.active_warrants_count || 0) > 0 || Number(person.felony_convictions_count || 0) > 0
                                ? "offender_residences"
                                : includesAny(`${person.intelligence_notes} ${person.patterns}`, ["traffick"])
                                    ? "human_trafficking"
                                    : "multiple_missing_persons",
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
                        analysisLayer: includesAny(`${person.intelligence_notes} ${person.patterns}`, ["child exploitation", "csam", "minor exploitation"])
                            ? "child_exploitation"
                            : "multiple_missing_persons",
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
                        analysisLayer: "multiple_missing_persons",
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
                        analysisLayer: person.gang_affiliations ? "gang_territories" : "multiple_missing_persons",
                    }
                    : null,
            ].filter(Boolean);
        }),
    ];
    const analyticalSightings = sightings.map((sighting) => ({
        ...sighting,
        analysis_layer: classifyExternalRecord({
            record_type: "sighting",
            notes: sighting.description,
            location: sighting.location,
        }),
    }));
    const analyticalRecords = externalRecords.map((record) => ({
        ...record,
        analysis_layer: classifyExternalRecord(record),
    }));
    const eventTitleForRecord = (record) => {
        const layer = record.analysis_layer || classifyExternalRecord(record);
        if (layer === "lpr_hits") return "License plate reader hit received";
        if (layer === "camera_hits") return "Camera detected vehicle or person";
        if (layer === "social_media") return "New social media lead";
        if (layer === "unidentified_remains") return "Medical examiner intelligence returned";
        if (includesAny(record.record_type, ["hospital"])) return "Hospital inquiry returned";
        if (includesAny(record.record_type, ["interagency", "agency", "report"])) return "Partner agency uploaded report";
        return `${String(record.record_type || "External intelligence").replaceAll("_", " ")} received`;
    };
    const liveEvents = [
        ...analyticalRecords.map((record) => ({
            id: `record-${record.id}`,
            timestamp: record.created_at || record.geocoded_at,
            title: eventTitleForRecord(record),
            detail: record.location || record.notes,
            source: "Partner source",
        })),
        ...evidence.map((item) => ({
            id: `evidence-${item.evidence_id}`,
            timestamp: item.created_at || item.available_at,
            title: includesAny(`${item.evidence_type} ${item.description}`, ["dna"])
                ? "DNA comparison completed"
                : `${item.evidence_type || "Evidence"} result updated`,
            detail: item.custody_status || item.description,
            source: "Evidence / lab",
        })),
        ...sightings.map((sighting, index) => ({
            id: `sighting-${sighting.sighting_id || index}`,
            timestamp: sighting.created_at || sighting.sighting_time,
            title: includesAny(sighting.description, ["camera", "lpr", "plate"])
                ? "Automated detection received"
                : "New sighting reported",
            detail: sighting.location,
            source: "Sighting",
        })),
        ...bolos.map((bolo, index) => ({
            id: `bolo-${bolo.bolo_id || index}`,
            timestamp: bolo.created_at,
            title: bolo.title || "BOLO intelligence updated",
            detail: bolo.last_known_location,
            source: "BOLO",
        })),
    ]
        .filter((event) => event.timestamp)
        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
        .slice(0, 12);
    const exampleLiveEvents = [
        ["7:15 PM", "Houston PD uploaded report"],
        ["7:12 PM", "Hospital inquiry returned"],
        ["7:09 PM", "DNA comparison completed"],
        ["7:03 PM", "Camera detected vehicle"],
        ["6:58 PM", "New social media lead"],
    ].map(([time, title], index) => ({ id: `example-${index}`, displayTime: time, title }));
    const intelligenceEvents = liveEvents.length > 0 ? liveEvents : exampleLiveEvents;
    const eventTime = (event) => {
        if (event.displayTime) return event.displayTime;
        const date = new Date(event.timestamp);
        return Number.isNaN(date.getTime())
            ? "Now"
            : date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
    };
    const correlationSignals = [
        ...sightings.map((sighting) => ({
            caseId: sighting.case_id,
            location: sighting.location,
            relationship: "Reported at the same location",
            confidence: Number(sighting.confidence_score || 0.72),
        })),
        ...externalRecords.map((record) => ({
            caseId: record.case_id,
            location: record.geocoded_address || record.location,
            relationship: "Shared intelligence location",
            confidence: record.geocode_score ? Number(record.geocode_score) / 100 : 0.68,
        })),
    ].filter((signal) => signal.caseId && signal.location);
    const signalsByLocation = correlationSignals.reduce((groups, signal) => {
        const key = signal.location.trim().toLowerCase().replace(/[^a-z0-9]/g, "");
        if (!key) return groups;
        return { ...groups, [key]: [...(groups[key] || []), signal] };
    }, {});
    const detectedCorrelations = Object.values(signalsByLocation)
        .map((signals, index) => {
            const caseIds = [...new Set(signals.map((signal) => signal.caseId))];
            if (caseIds.length < 2) return null;
            return {
                id: `location-correlation-${index}`,
                caseA: `Case ${caseIds[0]}`,
                caseB: `Case ${caseIds[1]}`,
                relationship: signals[0].relationship,
                sharedValue: signals[0].location,
                ownerLabel: "Cross-case location",
                owner: `${signals.length} linked records`,
                confidence: Math.min(0.98, Math.max(...signals.map((signal) => signal.confidence)) + 0.08),
            };
        })
        .filter(Boolean)
        .sort((a, b) => b.confidence - a.confidence)
        .slice(0, 5);
    const representativeCorrelations = [
        {
            id: "example-motel-vehicle",
            caseA: "Case MP-2026-014",
            caseB: "Case MP-2025-033",
            relationship: "Victim visited the same motel",
            sharedValue: "Shared vehicle: White Tahoe",
            ownerLabel: "Registered owner",
            owner: "John Smith",
            confidence: 0.92,
        },
        {
            id: "example-camera-location",
            caseA: "Case MP-2026-021",
            caseB: "Case MP-2026-008",
            relationship: "Camera and LPR signals overlap",
            sharedValue: "North transit corridor",
            ownerLabel: "Vehicle pattern",
            owner: "Three detections in 48 hours",
            confidence: 0.87,
        },
        {
            id: "example-social-associate",
            caseA: "Case MP-2025-119",
            caseB: "Case MP-2026-017",
            relationship: "Shared social media associate",
            sharedValue: "Two linked accounts",
            ownerLabel: "Pattern",
            owner: "Common contact and location history",
            confidence: 0.81,
        },
    ];
    const aiCorrelations = detectedCorrelations.length > 0
        ? detectedCorrelations
        : representativeCorrelations;
    const topAiConfidence = Math.round((aiCorrelations[0]?.confidence || 0) * 100);

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
                    <div className="intelligence-map-heading">
                        <div>
                            <span>Cross-case pattern workspace</span>
                            <h2>Analytical Intelligence Map</h2>
                            <p>Explore concentrations, relationships, repeat locations, and integrated intelligence signals.</p>
                        </div>
                    </div>
                    <Suspense fallback={<div className="intelligence-map-loading">Loading analytical map…</div>}>
                        <IntelligenceMap3D
                            sightings={analyticalSightings}
                            records={analyticalRecords}
                            mappedLocations={mappedLocations}
                        />
                    </Suspense>
                </section>

                <aside className="intelligence-right-rail">
                <section className="intelligence-panel">
                    <div className="intelligence-stream-heading">
                        <span>Live Intelligence</span>
                        <i aria-hidden="true"></i>
                    </div>
                    <div className="intelligence-event-stream">
                        {intelligenceEvents.map((event) => (
                            <article key={event.id}>
                                <time dateTime={event.timestamp}>{eventTime(event)}</time>
                                <div>
                                    <strong>{event.title}</strong>
                                    {event.detail && <p>{event.detail}</p>}
                                    {event.source && <small>{event.source}</small>}
                                </div>
                            </article>
                        ))}
                    </div>
                </section>
                <section className="intelligence-panel beacon-ai-panel">
                    <div className="beacon-ai-heading">
                        <div>
                            <span>Beacon AI</span>
                            <small>{detectedCorrelations.length > 0 ? "Live correlation analysis" : "Representative preview"}</small>
                        </div>
                        <i aria-hidden="true">AI</i>
                    </div>
                    <p className="beacon-ai-finding-count">
                        <strong>{aiCorrelations.length}</strong>
                        investigative correlations found
                    </p>
                    <div className="beacon-ai-confidence">
                        <span>Confidence</span>
                        <strong>{topAiConfidence}%</strong>
                        <div><i style={{ width: `${topAiConfidence}%` }}></i></div>
                    </div>
                    <button
                        type="button"
                        className="beacon-ai-review-button"
                        onClick={() => setShowAiReview((current) => !current)}
                    >
                        {showAiReview ? "Close Review" : "Click to Review"}
                    </button>
                    {showAiReview && (
                        <div className="beacon-ai-correlation-list">
                            {aiCorrelations.map((correlation) => (
                                <article key={correlation.id}>
                                    <div className="beacon-ai-case-pair">
                                        <strong>{correlation.caseA}</strong>
                                        <span>linked with</span>
                                        <strong>{correlation.caseB}</strong>
                                    </div>
                                    <p>{correlation.relationship}</p>
                                    <dl>
                                        <div><dt>Shared signal</dt><dd>{correlation.sharedValue}</dd></div>
                                        <div><dt>{correlation.ownerLabel}</dt><dd>{correlation.owner}</dd></div>
                                        <div><dt>Confidence</dt><dd>{Math.round(correlation.confidence * 100)}%</dd></div>
                                    </dl>
                                </article>
                            ))}
                        </div>
                    )}
                </section>
                </aside>
            </div>
        </div>
    );
}

export default IntelligenceCenter;
