import React from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";


//SIGHTING MAP COMPONENT TO DISPLAY SIGHTINGS ON A MAP
function SightingMap({ sightings }) {

    const validSightings = sightings.filter(

        (s) => s.latitude && s.longitude
    );

    if (validSightings.length === 0) {

        return <p>No mapped sightings yet.</p>;
    }

    return (

        <MapContainer

            center={[validSightings[0].latitude, validSightings[0].longitude]}

            zoom={12}

            style={{ height: "400px", width: "100%" }}
        >
            <TileLayer

                attribution='&copy; OpenStreetMap contributors'

                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {validSightings.map((sighting) => (

                <Marker

                    key={sighting.sighting_id}

                    position={[sighting.latitude, sighting.longitude]}
                >
                    <Popup>

                        <strong>{sighting.location}</strong>

                        <br />

                        {sighting.description}

                        <br />

                        Confidence: {sighting.confidence_score}

                    </Popup>

                </Marker>
            ))}
        </MapContainer>
    );
}

export default SightingMap;