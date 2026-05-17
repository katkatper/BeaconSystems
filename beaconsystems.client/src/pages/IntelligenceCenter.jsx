import React, { useEffect, useState } from "react";
import SightingMap from "./SightingMap.jsx";



function IntelligenceCenter() {

    const [sightings, setSightings] = useState([]);
    const [minimumConfidence, setMinimumConfidence] = useState(0);
    const [selectedCaseId, setSelectedCaseId] = useState("all");


    useEffect(() => {

        const token = localStorage.getItem("token");

        fetch("http://127.0.0.1:8000/sightings/", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        })
            .then((res) => res.json())
            .then((data) => {
                setSightings(data);
            })
            .catch((err) => {
                console.error(err);
            });

    }, []);



    const filteredSightings = sightings.filter((sighting) => {

        const matchesConfidence =
            (sighting.confidence_score ?? 0) >= minimumConfidence;

        const matchesCase =
            selectedCaseId === "all" ||
            String(sighting.case_id) === selectedCaseId;

        return matchesConfidence && matchesCase;
    });


    return (
        <div>

            <h1>Beacon Intelligence Center</h1>

            <p>
                Live operational intelligence map displaying
                sightings, movement paths, confidence levels,
                and estimated search radiuses.
            </p>

            <div style={{ marginBottom: "15px" }}>

                <label>Minimum Confidence: </label>

                <select
                    value={minimumConfidence}
                    onChange={(e) =>
                        setMinimumConfidence(Number(e.target.value))
                    }
                >
                    <option value={0}>All</option>
                    <option value={0.5}>Medium +</option>
                    <option value={0.8}>High Only</option>
                </select>

            </div>


            <div style={{ marginBottom: "15px" }}>

                <label>Filter By Case: </label>

                <select
                    value={selectedCaseId}
                    onChange={(e) => setSelectedCaseId(e.target.value)}
                >
                    <option value="all">All Cases</option>

                    {[...new Set(sightings.map((s) => s.case_id))]
                        .filter(Boolean)
                        .map((caseId) => (
                            <option key={caseId} value={caseId}>
                                Case #{caseId}
                            </option>
                        ))}
                </select>

            </div>

            <SightingMap sightings={filteredSightings} />

        </div>
    );
}

export default IntelligenceCenter;