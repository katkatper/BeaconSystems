const AUTH_SESSION_KEYS = [
    "token",
    "role",
    "username",
    "agency_id",
    "last_activity_at",
    "session_expires_at",
    "session_timeout_message",
];

export const getSessionValue = (key, fallback = null) => (
    sessionStorage.getItem(key) ?? fallback
);

export const setSessionValue = (key, value) => {
    if (value === null || value === undefined || value === "") {
        sessionStorage.removeItem(key);
        return;
    }
    sessionStorage.setItem(key, String(value));
};

export const storeAuthSession = (data) => {
    setSessionValue("token", data.access_token);
    setSessionValue("role", data.role);
    setSessionValue("username", data.username);
    setSessionValue("agency_id", data.agency_id);
    setSessionValue("last_activity_at", Date.now());
    setSessionValue("session_expires_at", data.session_expires_at);
};

export const updateSessionIdentity = (data) => {
    setSessionValue("role", data.role);
    setSessionValue("username", data.username);
    setSessionValue("agency_id", data.agency_id);
};

export const clearAuthSession = ({ message } = {}) => {
    AUTH_SESSION_KEYS.forEach((key) => sessionStorage.removeItem(key));
    if (message) setSessionValue("session_timeout_message", message);
};

export const hasAuthToken = () => Boolean(getSessionValue("token"));
