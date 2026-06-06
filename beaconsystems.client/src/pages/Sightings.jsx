import React, { useEffect, useState } from "react";
import SightingMap from "./SightingMap.jsx";

function Sightings() {
    const [sightings, setSightings] = useState([]);
    const [showMore, setShowMore] = useState(false);

    useEffect(() => {
        let isMounted = true;
        const token = localStorage.getItem("token");

        fetch("http://127.0.0.1:8000/sightings/", {
            headers: { Authorization: `Bearer ${token}` },
        })
            .then((response) => (response.ok ? response.json() : []))
            .then((data) => {
                if (isMounted) {
                    setSightings(Array.isArray(data) ? data : []);
                }
            })
            .catch((err) => console.error(err));

        return () => {
            isMounted = false;
        };
    }, []);

    const sortedSightings = [...sightings].sort(
        (a, b) =>
            new Date(b.sighting_time || b.created_at) -
            new Date(a.sighting_time || a.created_at)
    );
    const visibleSightings = sortedSightings.slice(0, showMore ? 8 : 2);

    return (
        <div className="sightings-page beacon-page">
            <section className="beacon-page-header">
                <h1>Sightings</h1>
                <p>Review field sightings, locations, confidence, and case links.</p>
            </section>

            <section className="beacon-three-panel">
                <article className="beacon-panel beacon-panel-wide">
                    <div className="dashboard-panel-header">
                        <span>Activity Map</span>
                        <strong>{sightings.length} sightings</strong>
                    </div>
                    <SightingMap sightings={sortedSightings} />
                </article>

                <article className="beacon-panel">
                    <div className="dashboard-panel-header">
                        <span>Recent Sightings</span>
                        <button type="button" onClick={() => setShowMore((current) => !current)}>
                            {showMore ? "Show 2" : "Show more"}
                        </button>
                    </div>

                    {visibleSightings.length === 0 ? (
                        <p>No sightings available.</p>
                    ) : (
                        <div className="compact-card-list">
                            {visibleSightings.map((sighting) => (
                                <article key={sighting.sighting_id} className="queue-item">
                                    <div>
                                        <strong>{sighting.location || "Unknown location"}</strong>
                                        <span>Case {sighting.case_id}</span>
                                    </div>
                                    <p>{sighting.description || "No description provided."}</p>
                                    <small>
                                        Confidence {sighting.confidence_score ?? "unknown"} |{" "}
                                        {sighting.sighting_time || sighting.created_at || "No timestamp"}
                                    </small>
                                </article>
                            ))}
                        </div>
                    )}
                </article>

                <article className="beacon-panel">
                    <h2>Sighting Review</h2>
                    <div className="beacon-status-list">
                        <span>High confidence: {sightings.filter((item) => Number(item.confidence_score) >= 0.8).length}</span>
                        <span>Needs follow-up: {sightings.filter((item) => !item.confidence_score).length}</span>
                        <span>Linked cases: {new Set(sightings.map((item) => item.case_id).filter(Boolean)).size}</span>
                    </div>
                </article>
            </section>
        </div>
    );
}

export default Sightings;
