const API_BASE = "http://107.23.83.139:8000";

export async function getHealth() {
    const response = await fetch(`${API_BASE}/`);
    if (!response.ok) {
        throw new Error("Failed to fetch backend");
    }
    return response.json();
}

export async function createPerson(payload) {
    const response = await fetch(`${API_BASE}/persons`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Failed to create person");
    }

    return response.json();
}