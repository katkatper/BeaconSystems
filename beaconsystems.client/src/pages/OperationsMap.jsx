import React, { useEffect, useMemo, useState } from "react";
import { Circle, MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import { isUsCoordinate } from "../geoUtils.js";

const layerDefinitions = [
    ["active_cases", "Active investigations", "#22c55e", "C"],
    ["high_risk_cases", "High-risk cases", "#ef4444", "!"],
    ["recent_sightings", "Recent sightings", "#facc15", "S"],
    ["officer_locations", "Officer locations", "#3b82f6", "O"],
    ["interagency_requests", "Interagency requests", "#a855f7", "I"],
    ["road_closures", "Road closures", "#e5e7eb", "R"],
    ["alert_regions", "AMBER / Silver regions", "#f97316", "A"],
    ["hospital_inquiries", "Hospital inquiries", "#10b981", "H"],
];

const layerById = new Map(layerDefinitions.map(([id, label, color, symbol]) => [
    id,
    { id, label, color, symbol },
]));

function createOperationsIcon(layer) {
    const definition = layerById.get(layer) || layerById.get("active_cases");
    return L.divIcon({
        className: "operations-map-marker",
        html: `<div style="--operation-color:${definition.color}">${definition.symbol}</div>`,
        iconSize: [34, 34],
        iconAnchor: [17, 17],
    });
}

function FitOperationsMap({ locations }) {
    const map = useMap();

    useEffect(() => {
        map.invalidateSize();
        const positions = locations.map((location) => [location.latitude, location.longitude]);
        if (positions.length === 1) map.setView(positions[0], 12, { animate: false });
        if (positions.length > 1) map.fitBounds(positions, { padding: [45, 45], maxZoom: 12 });
    }, [locations, map]);

    return null;
}

function OperationsMap({ data = {} }) {
    const integrations = data.integrations || {};
    const [enabledLayers, setEnabledLayers] = useState(() => new Set(
        layerDefinitions
            .filter(([id]) => !["officer_locations", "road_closures"].includes(id))
            .map(([id]) => id)
    ));
    const locations = useMemo(() => (data.locations || [])
        .filter((location) =>
            Number.isFinite(Number(location.latitude)) &&
            Number.isFinite(Number(location.longitude)) &&
            isUsCoordinate(location.latitude, location.longitude)
        )
        .map((location) => ({
            ...location,
            latitude: Number(location.latitude),
            longitude: Number(location.longitude),
        })), [data.locations]);
    const visibleLocations = locations.filter((location) => enabledLayers.has(location.layer));
    const counts = locations.reduce((result, location) => ({
        ...result,
        [location.layer]: (result[location.layer] || 0) + 1,
    }), {});

    const toggleLayer = (layerId) => {
        setEnabledLayers((current) => {
            const next = new Set(current);
            if (next.has(layerId)) next.delete(layerId);
            else next.add(layerId);
            return next;
        });
    };

    return (
        <div className="operations-map-workspace">
            <div className="operations-map-toolbar" aria-label="Operations map layers">
                {layerDefinitions.map(([id, label, color]) => {
                    const integrationUnavailable =
                        (id === "officer_locations" && !integrations.officer_locations) ||
                        (id === "road_closures" && !integrations.road_closures);
                    return (
                        <button
                            key={id}
                            type="button"
                            className={enabledLayers.has(id) ? "active" : ""}
                            onClick={() => toggleLayer(id)}
                            disabled={integrationUnavailable}
                            title={integrationUnavailable ? "Integration not configured" : `Toggle ${label}`}
                        >
                            <i style={{ backgroundColor: color }}></i>
                            <span>{label}</span>
                            <strong>{integrationUnavailable ? "—" : counts[id] || 0}</strong>
                        </button>
                    );
                })}
            </div>

            <div className="operations-map-shell">
                <MapContainer center={[32.7767, -96.797]} zoom={7} className="operations-map">
                    <TileLayer
                        attribution="Map data (c) OpenStreetMap contributors"
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    <FitOperationsMap locations={visibleLocations} />
                    {visibleLocations.map((location) => (
                        <React.Fragment key={location.id}>
                            {location.layer === "alert_regions" && (
                                <Circle
                                    center={[location.latitude, location.longitude]}
                                    radius={16093}
                                    pathOptions={{
                                        color: layerById.get(location.layer).color,
                                        fillOpacity: 0.09,
                                        weight: 2,
                                    }}
                                />
                            )}
                            <Marker
                                position={[location.latitude, location.longitude]}
                                icon={createOperationsIcon(location.layer)}
                            >
                                <Popup>
                                    <strong>{location.label}</strong>
                                    <br />
                                    {location.detail || layerById.get(location.layer)?.label}
                                    {location.case_number && <><br />Case: {location.case_number}</>}
                                    {location.confidence !== undefined && location.confidence !== null && (
                                        <><br />Confidence: {Math.round(Number(location.confidence) * (Number(location.confidence) <= 1 ? 100 : 1))}%</>
                                    )}
                                </Popup>
                            </Marker>
                        </React.Fragment>
                    ))}
                </MapContainer>
                {visibleLocations.length === 0 && (
                    <div className="operations-map-empty">No mapped operational activity is available for the selected layers.</div>
                )}
            </div>
        </div>
    );
}

export default OperationsMap;
