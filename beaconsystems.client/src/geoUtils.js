const knownLocations = {
    "1001 california st houston tx 77006": [29.7436, -95.3913],
    "montrose library": [29.7436, -95.3913],
    "2510 willowick rd houston tx 77027": [29.7418, -95.4502],
    "2510 willowick road houston tx 77027": [29.7418, -95.4502],
    "1200 travis street houston tx 77002": [29.7543, -95.367],
    "715 e 8th street austin tx 78701": [30.2718, -97.7345],
    "1400 botham jean blvd dallas tx 75215": [32.7696, -96.7954],
    "12230 west road houston tx 77065": [29.9147, -95.604],
    "5805 north lamar blvd austin tx 78752": [30.3254, -97.7247],
    "5700 east northwest highway dallas tx 75231": [32.8648, -96.7676],
    "bayside market place": [25.7783, -80.186],
    "bayside marketplace": [25.7783, -80.186],
    "1015 n america way miami fl 33132": [25.7778, -80.1799],
    "1015 north america way miami fl 33132": [25.7778, -80.1799],
};

const cityCenters = {
    houston: [29.7604, -95.3698],
    dallas: [32.7767, -96.797],
    austin: [30.2672, -97.7431],
    "san antonio": [29.4241, -98.4936],
    "el paso": [31.7619, -106.485],
    "fort worth": [32.7555, -97.3308],
    miami: [25.7617, -80.1918],
};

export function normalizeLocation(value) {
    return String(value || "")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, " ")
        .trim();
}

function parseCoordinatePair(value) {
    const match = String(value || "").match(/^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$/);

    if (!match) return null;

    const latitude = Number(match[1]);
    const longitude = Number(match[2]);

    if (Number.isFinite(latitude) && Number.isFinite(longitude) && latitude >= -90 && latitude <= 90 && longitude >= -180 && longitude <= 180) {
        return { latitude, longitude, accuracy: "provided_coordinates" };
    }

    return null;
}

function hashOffset(value) {
    let hash = 17;

    for (const character of value) {
        hash = (hash * 31 + character.charCodeAt(0)) % 1000003;
    }

    const latSeed = (hash % 997) / 997;
    const lonSeed = ((hash * 37) % 991) / 991;

    return [(latSeed - 0.5) * 0.035, (lonSeed - 0.5) * 0.035];
}

export function geocodeLocal(value) {
    const normalized = normalizeLocation(value);

    if (!normalized) return null;

    const coordinates = parseCoordinatePair(value);

    if (coordinates) return coordinates;

    if (knownLocations[normalized]) {
        const [latitude, longitude] = knownLocations[normalized];
        return { latitude, longitude, accuracy: "known_address" };
    }

    const knownMatch = Object.entries(knownLocations).find(([key]) => key.includes(normalized) || normalized.includes(key));

    if (knownMatch) {
        const [latitude, longitude] = knownMatch[1];
        return { latitude, longitude, accuracy: "known_place" };
    }

    const cityMatch = Object.entries(cityCenters).find(([city]) => normalized.includes(city));

    if (cityMatch) {
        const [latitude, longitude] = cityMatch[1];
        const [latOffset, lonOffset] = hashOffset(normalized);
        return {
            latitude: latitude + latOffset,
            longitude: longitude + lonOffset,
            accuracy: "city_estimate",
        };
    }

    return null;
}
