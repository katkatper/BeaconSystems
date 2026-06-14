export const API_BASE =
    import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function getHealth() {
    return apiGet("/");
}

export async function createPerson(payload) {
    return apiPost("/persons/", payload);
}

export function authHeaders(extraHeaders = {}) {
    const token = localStorage.getItem("token");

    return {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...extraHeaders,
    };
}

export function apiUrl(path) {
    if (path.startsWith("http")) {
        return path;
    }

    return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

async function parseResponse(response) {
    const contentType = response.headers.get("content-type") || "";

    if (!response.ok) {
        const errorData = contentType.includes("application/json")
            ? await response.json().catch(() => ({}))
            : {};
        const fallback = await response.text().catch(() => "");
        throw new Error(errorData.detail || fallback || `Request failed (${response.status})`);
    }

    if (contentType.includes("application/json")) {
        return response.json();
    }

    return response;
}

export async function apiRequest(path, options = {}) {
    const response = await fetch(apiUrl(path), {
        ...options,
        headers: authHeaders(options.headers || {}),
    });

    return parseResponse(response);
}

export async function apiGet(path) {
    return apiRequest(path);
}

export async function apiPost(path, payload) {
    return apiRequest(path, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });
}

export async function apiPostForm(path, formData) {
    return apiRequest(path, {
        method: "POST",
        body: formData,
    });
}

export async function apiBlob(path) {
    const response = await fetch(apiUrl(path), {
        headers: authHeaders(),
    });

    if (!response.ok) {
        throw new Error(`Request failed (${response.status})`);
    }

    return response.blob();
}
