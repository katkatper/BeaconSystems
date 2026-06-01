import React, { useEffect } from "react";
import {
    Circle,
    MapContainer,
    Marker,
    Polygon,
    Polyline,
    Popup,
    TileLayer,
    useMap,
} from "react-leaflet";
import L from "leaflet";

function getConfidenceLevel(confidence) {
    const score = Number(confidence);

    if (score >= 0.8) return "high";
    if (score >= 0.5) return "medium";
    return "low";
}

function getConfidenceColor(confidence) {
    const level = getConfidenceLevel(confidence);

    if (level === "high") return "#ef4444";
    if (level === "medium") return "#f59e0b";
    return "#94a3b8";
}

function getSearchRadius(confidence) {
    if (confidence >= 0.8) return 500;
    if (confidence >= 0.5) return 1000;
    return 1500;
}

function createMarkerIcon(confidence, index) {
    return L.divIcon({
        className: "custom-marker sighting-marker-3d",
        html: `
            <div class="sighting-pin" style="--pin-color:${getConfidenceColor(confidence)};">
                ${index + 1}
            </div>
        `,
        iconSize: [34, 48],
        iconAnchor: [17, 44],
    });
}

function createArrowIcon(angle) {
    return L.divIcon({
        className: "direction-arrow",
        html: `<div class="route-arrow" style="transform: rotate(${angle}deg);"></div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
    });
}

function FitMapToSightings({ positions }) {
    const map = useMap();

    useEffect(() => {
        if (positions.length > 0) {
            map.fitBounds(positions, { padding: [40, 40] });
        }
    }, [positions, map]);

    return null;
}

function buildSearchedArea(validSightings) {
    if (validSightings.length === 0) return [];

    const latitudes = validSightings.map((s) => Number(s.latitude));
    const longitudes = validSightings.map((s) => Number(s.longitude));
    const minLat = Math.min(...latitudes);
    const maxLat = Math.max(...latitudes);
    const minLng = Math.min(...longitudes);
    const maxLng = Math.max(...longitudes);
    const padding = Math.max((maxLat - minLat + maxLng - minLng) / 4, 0.012);

    return [
        [minLat - padding, minLng - padding],
        [minLat - padding, maxLng + padding],
        [maxLat + padding, maxLng + padding],
        [maxLat + padding, minLng - padding],
    ];
}

function SightingMap({ sightings }) {
    const validSightings = sightings
        .filter(
            (s) =>
                Number.isFinite(Number(s.latitude)) &&
                Number.isFinite(Number(s.longitude))
        )
        .map((s) => ({
            ...s,
            latitude: Number(s.latitude),
            longitude: Number(s.longitude),
        }))
        .sort(
            (a, b) =>
                new Date(a.sighting_time || a.created_at) -
                new Date(b.sighting_time || b.created_at)
        );

    const pathPositions = validSightings.map((s) => [
        s.latitude,
        s.longitude,
    ]);

    const arrowPositions = [];

    for (let i = 0; i < pathPositions.length - 1; i++) {
        const start = pathPositions[i];
        const end = pathPositions[i + 1];
        const midLat = (start[0] + end[0]) / 2;
        const midLng = (start[1] + end[1]) / 2;
        const deltaLat = end[0] - start[0];
        const deltaLng = end[1] - start[1];
        const angle = Math.atan2(deltaLat, deltaLng) * (180 / Math.PI);

        arrowPositions.push({
            position: [midLat, midLng],
            angle: -angle,
        });
    }

    if (validSightings.length === 0) {
        return <p>No mapped sightings yet.</p>;
    }

    const searchedArea = buildSearchedArea(validSightings);

    return (
        <div className="sighting-map-workspace">
            <div className="sighting-map-3d-shell">
                <MapContainer
                    center={[32.78, -96.79]}
                    zoom={11}
                    className="sighting-map-3d"
                >
                    <TileLayer
                        attribution="Map data (c) OpenStreetMap contributors"
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />

                    <FitMapToSightings positions={pathPositions} />

                    {searchedArea.length > 0 && (
                        <Polygon
                            positions={searchedArea}
                            pathOptions={{
                                color: "#38bdf8",
                                fillColor: "#38bdf8",
                                fillOpacity: 0.08,
                                opacity: 0.55,
                                weight: 2,
                                dashArray: "8 8",
                            }}
                        />
                    )}

                    {validSightings.map((sighting, index) => (
                        <Circle
                            key={`circle-${sighting.sighting_id ?? index}`}
                            center={[sighting.latitude, sighting.longitude]}
                            radius={getSearchRadius(sighting.confidence_score)}
                            pathOptions={{
                                color: getConfidenceColor(sighting.confidence_score),
                                fillColor: getConfidenceColor(sighting.confidence_score),
                                weight: 2,
                                fillOpacity: 0.14,
                            }}
                        />
                    ))}

                    {pathPositions.length > 1 && (
                        <Polyline
                            positions={pathPositions}
                            pathOptions={{
                                color: "#93c5fd",
                                dashArray: "10 8",
                                weight: 4,
                                opacity: 0.88,
                            }}
                        />
                    )}

                    {arrowPositions.map((arrow, index) => (
                        <Marker
                            key={`arrow-${index}`}
                            position={arrow.position}
                            icon={createArrowIcon(arrow.angle)}
                        />
                    ))}

                    {validSightings.map((sighting, index) => (
                        <Marker
                            key={sighting.sighting_id ?? `sighting-${index}`}
                            position={[sighting.latitude, sighting.longitude]}
                            icon={createMarkerIcon(
                                sighting.confidence_score,
                                index
                            )}
                        >
                            <Popup>
                                <strong>
                                    Sighting #{index + 1}: {sighting.location}
                                </strong>
                                <br />
                                {sighting.description}
                                <br />
                                Confidence:{" "}
                                {sighting.confidence_score ?? "Unknown"}
                                <br />
                                Search radius:{" "}
                                {getSearchRadius(sighting.confidence_score)} meters
                                <br />
                                Time: {sighting.sighting_time || sighting.created_at}
                            </Popup>
                        </Marker>
                    ))}
                </MapContainer>
            </div>

            <div className="sighting-map-legend">
                <span>
                    <i className="legend-dot high"></i>
                    High confidence
                </span>
                <span>
                    <i className="legend-dot medium"></i>
                    Medium confidence
                </span>
                <span>
                    <i className="legend-dot low"></i>
                    Low or unknown
                </span>
                <span>
                    <i className="legend-ring"></i>
                    Search radius
                </span>
                <span>
                    <i className="legend-line"></i>
                    Possible route
                </span>
                <span>
                    <i className="legend-area"></i>
                    Searched area
                </span>
            </div>
        </div>
    );
}

export default SightingMap;
