const AUTH_SESSION_KEYS = [
    "token",
    "role",
    "username",
    "agency_id",
    "last_activity_at",
    "session_expires_at",
    "session_timeout_message",
];

let verifiedToken = null;
let pendingVerification = null;

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
    verifiedToken = null;
    pendingVerification = null;
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

export const verifySessionIdentity = (token, verifier) => {
    if (verifiedToken === token) return Promise.resolve();
    if (pendingVerification?.token === token) return pendingVerification.promise;

    const promise = Promise.resolve()
        .then(verifier)
        .then((identity) => {
            if (getSessionValue("token") !== token) {
                throw new Error("Session changed during identity verification");
            }
            updateSessionIdentity(identity);
            verifiedToken = token;
        })
        .finally(() => {
            if (pendingVerification?.token === token) pendingVerification = null;
        });
    pendingVerification = { token, promise };
    return promise;
};

export const clearAuthSession = ({ message } = {}) => {
    verifiedToken = null;
    pendingVerification = null;
    AUTH_SESSION_KEYS.forEach((key) => sessionStorage.removeItem(key));
    if (message) setSessionValue("session_timeout_message", message);
};

export const hasAuthToken = () => Boolean(getSessionValue("token"));
