import { getSessionValue, setSessionValue } from "./authSession.js";

export const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
let pendingRefresh = null;

export async function getHealth() {
    return apiGet("/");
}

export async function createPerson(payload) {
    return apiPost("/persons/", payload);
}

export function authHeaders(extraHeaders = {}) {
    const token = getSessionValue("token");

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
        const error = new Error(errorData.detail || fallback || `Request failed (${response.status})`);
        error.status = response.status;
        throw error;
    }

    if (contentType.includes("application/json")) {
        return response.json();
    }

    return response;
}

async function refreshAccessToken() {
    if (pendingRefresh) return pendingRefresh;

    const tokenBeingRefreshed = getSessionValue("token");

    pendingRefresh = fetch(apiUrl("/users/refresh"), {
        method: "POST",
        credentials: "include",
    })
        .then(async (response) => {
            if (!response.ok) return false;
            const refreshed = await response.json();
            if (getSessionValue("token") !== tokenBeingRefreshed) return false;
            setSessionValue("token", refreshed.access_token);
            setSessionValue("session_expires_at", refreshed.session_expires_at);
            return true;
        })
        .finally(() => {
            pendingRefresh = null;
        });

    return pendingRefresh;
}

export async function apiRequest(path, options = {}, allowRefresh = true) {
    let response = await fetch(apiUrl(path), {
        ...options,
        credentials: "include",
        headers: authHeaders(options.headers || {}),
    });

    if (response.status === 401 && allowRefresh && path !== "/users/refresh") {
        if (await refreshAccessToken()) {
            response = await fetch(apiUrl(path), {
                ...options,
                credentials: "include",
                headers: authHeaders(options.headers || {}),
            });
        }
    }

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

export async function apiPatch(path, payload) {
    return apiRequest(path, {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });
}

export async function apiPut(path, payload) {
    return apiRequest(path, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });
}

export async function apiDelete(path) {
    return apiRequest(path, { method: "DELETE" });
}

export async function apiPostForm(path, formData) {
    return apiRequest(path, {
        method: "POST",
        body: formData,
    });
}

export async function apiBlob(path) {
    const response = await apiRequest(path);
    return response instanceof Response ? response.blob() : response;
}
