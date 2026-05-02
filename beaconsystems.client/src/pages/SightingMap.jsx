import React, { useEffect } from "react";
import {MapContainer, TileLayer, Marker,Popup,Polyline,Circle, useMap} from "react-leaflet";
import L from "leaflet";

function getPinColor(confidence) {
    if (confidence >= 0.8) return "red";
    if (confidence >= 0.5) return "orange";
    return "gray";
}

function getSearchRadius(confidence) {
    if (confidence >= 0.8) return 500;
    if (confidence >= 0.5) return 1000;
    return 1500;
}

function createMarkerIcon(confidence, index) {
    const color = getPinColor(confidence);


    return L.divIcon({

        className: "custom-marker",

        html: `
            <div style="
                background:${color};
                width:28px;
                height:28px;
                border-radius:50%;
                border:3px solid white;
                box-shadow:0 0 6px rgba(0,0,0,0.5);
                color:white;
                font-weight:bold;
                display:flex;
                align-items:center;
                justify-content:center;
                font-size:13px;
            ">
                ${index + 1}
            </div>
        `,
        iconSize: [28, 28],

        iconAnchor: [14, 14],
    });
}

function createArrowIcon(angle) {

    return L.divIcon({
        className: "direction-arrow",
        html: `
            <div style="
                font-size:24px;
                color:black;
                transform: rotate(${angle}deg);
            ">
                ➤
            </div>
        `,
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
function SightingMap({ sightings }) {

    const validSightings = sightings
        .filter(
            (s) => s.latitude && s.longitude
        )
        .sort(
            (a, b) =>
                new Date(
                    a.sighting_time || a.created_at
                ) -
                new Date(
                    b.sighting_time || b.created_at
                )
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

    return (
        <div>
            <p>
                <strong>Map Legend:</strong> Red = High confidence, Orange =

                Medium confidence, Gray = Low/Unknown. Circles show estimated

                search radius.
            </p>

            <MapContainer
                center={[32.78, -96.79]}

                zoom={11}

                style={{ height: "450px", width: "100%" }}
            >
                <TileLayer
                    attribution="Map data © OpenStreetMap contributors"

                    url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
                />
                
                <FitMapToSightings positions={pathPositions} />


                {validSightings.map((sighting) => (

                    <Circle 
                        key={`circle-${sighting.sighting_id}`}

                        center={[sighting.latitude, sighting.longitude]}

                        radius={getSearchRadius(sighting.confidence_score)}

                        pathOptions={{

                            weight: 2,

                            fillOpacity: 0.15,
                        }}
                    />
                ))}


                {pathPositions.length > 1 && (

                    <Polyline
                        positions={pathPositions}

                        weight={4}

                        opacity={0.8}
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
                        key={sighting.sighting_id}

                        position={[

                            sighting.latitude,

                            sighting.longitude,
                        ]}

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
                            Time:
                            {" "}
                            {sighting.sighting_time || sighting.created_at}

                        </Popup>
                    </Marker>
                ))}
            </MapContainer>
        </div>
    );
}

export default SightingMap;