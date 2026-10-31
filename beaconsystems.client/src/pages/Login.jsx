import { apiUrl } from "../api.jsx";
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const LOGIN_ERROR_MESSAGES = {
    401: "Invalid username or password.",
    403: "This account or agency is inactive. Contact your Beacon administrator.",
    404: "Beacon's login service was not found. Confirm the frontend API address is configured.",
    429: "Too many sign-in attempts. Wait a few minutes and try again.",
    503: "Beacon authentication is temporarily unavailable. Try again shortly.",
};

async function loginError(response) {
    const payload = await response.json().catch(() => ({}));
    const message = LOGIN_ERROR_MESSAGES[response.status]
        || payload.detail
        || `Beacon could not complete sign-in (error ${response.status}).`;
    const error = new Error(message);
    error.status = response.status;
    return error;
}



function Login({ onLogin }) {

    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [error, setError] = useState("");
    const [message, setMessage] = useState(
        () => localStorage.getItem("session_timeout_message") || ""
    );
    const [recoveryMode, setRecoveryMode] = useState("");
    const [pendingToken, setPendingToken] = useState("");
    const [mfaToken, setMfaToken] = useState("");
    const [mfaCode, setMfaCode] = useState("");
    const [mfaEnrollment, setMfaEnrollment] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const navigate = useNavigate();

    const getLandingPath = (role) => {
        if (role === "agency_admin") {
            return "/supervisor";
        }

        return "/";
    };

    useEffect(() => {
        localStorage.removeItem("session_timeout_message");
    }, []);

    const storeSession = (data) => {
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("role", data.role);
        localStorage.setItem("username", data.username);
        localStorage.setItem("agency_id", data.agency_id || "");
        localStorage.setItem("last_activity_at", String(Date.now()));

        if (data.session_expires_at) {
            localStorage.setItem("session_expires_at", data.session_expires_at);
        }
    };

    const completeLogin = (data) => {
        storeSession(data);

        if (data.password_change_required) {
            setPendingToken(data.access_token);
            setMessage("Your password must be updated before continuing.");
            return;
        }

        if (onLogin) {
            onLogin(data.access_token);
        }

        navigate(getLandingPath(data.role));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (isSubmitting) return;

        setIsSubmitting(true);
        setError("");
        setMessage("");
        setMfaToken("");
        setMfaCode("");
        setMfaEnrollment(null);

        try {
            const response = await fetch(apiUrl("/users/login"), {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    username: username.trim(),
                    password: password,
                }),
            });

            if (!response.ok) {
                throw await loginError(response);
            }

            const data = await response.json();

            if (data.mfa_required) {
                setMfaToken(data.mfa_token);
                setMessage("Enter your Beacon MFA code to complete sign-in.");
                return;
            }

            if (data.mfa_enrollment_required) {
                const enrollmentResponse = await fetch(apiUrl("/users/mfa/enrollment/start"), {
                    method: "POST",
                    credentials: "include",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ mfa_token: data.mfa_token }),
                });
                if (!enrollmentResponse.ok) {
                    const enrollmentError = await enrollmentResponse.json().catch(() => ({}));
                    throw new Error(enrollmentError.detail || "Could not start MFA enrollment");
                }
                const enrollment = await enrollmentResponse.json();
                setMfaToken(data.mfa_token);
                setMfaEnrollment(enrollment);
                setMessage("Set up MFA before continuing to Beacon.");
                return;
            }

            completeLogin(data);
        } catch (err) {
            console.error(err);
            setError(
                err instanceof TypeError
                    ? "Cannot reach Beacon. Confirm the API is running and the frontend API address is configured."
                    : err.message || "Beacon could not complete sign-in."
            );
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleMfaEnrollment = async (e) => {
        e.preventDefault();
        if (isSubmitting) return;

        setIsSubmitting(true);
        setError("");
        setMessage("");

        try {
            const response = await fetch(apiUrl("/users/mfa/enrollment/complete"), {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ mfa_token: mfaToken, code: mfaCode }),
            });
            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.detail || "MFA enrollment failed");
            }
            const data = await response.json();
            setMfaToken("");
            setMfaCode("");
            setMfaEnrollment(null);
            completeLogin(data);
        } catch (err) {
            console.error(err);
            setError(err.message || "Could not complete MFA enrollment");
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleMfaVerify = async (e) => {
        e.preventDefault();
        if (isSubmitting) return;

        setIsSubmitting(true);
        setError("");
        setMessage("");

        try {
            const response = await fetch(apiUrl("/users/mfa/verify"), {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    mfa_token: mfaToken,
                    code: mfaCode,
                }),
            });

            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.detail || "MFA verification failed");
            }

            const data = await response.json();
            setMfaToken("");
            setMfaCode("");
            completeLogin(data);
        } catch (err) {
            console.error(err);
            setError(err.message || "Could not verify MFA code");
        } finally {
            setIsSubmitting(false);
        }
    };

    const handlePasswordChange = async (e) => {
        e.preventDefault();
        setError("");
        setMessage("");

        if (newPassword !== confirmPassword) {
            setError("New password and confirmation do not match");
            return;
        }

        if (isSubmitting) return;

        setIsSubmitting(true);
        try {
            const response = await fetch(apiUrl("/users/change-password"), {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${pendingToken}`,
                },
                body: JSON.stringify({
                    current_password: password,
                    new_password: newPassword,
                }),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || "Password update failed");
            }

            localStorage.clear();
            setPendingToken("");
            setPassword("");
            setNewPassword("");
            setConfirmPassword("");
            setMessage("Password updated. Sign in again to start a new secure session.");
        } catch (err) {
            console.error(err);
            setError(err.message || "Could not update password");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="login-page">
            <div className="login-card">
                <h1>Beacon</h1>

                {mfaEnrollment ? (
                    <form className="mfa-challenge-panel" onSubmit={handleMfaEnrollment} aria-busy={isSubmitting}>
                        <h2>MFA Enrollment Required</h2>
                        <p>Add this account to your authenticator app, then enter its six-digit code.</p>
                        <div className="mfa-secret-box">
                            <span>Issuer: {mfaEnrollment.issuer}</span>
                            <span>Account: {mfaEnrollment.account}</span>
                            <strong>{mfaEnrollment.secret}</strong>
                            <small>{mfaEnrollment.otpauth_uri}</small>
                        </div>
                        <input
                            type="text"
                            inputMode="numeric"
                            autoComplete="one-time-code"
                            aria-label="Authenticator verification code"
                            placeholder="Six-digit code"
                            value={mfaCode}
                            onChange={(e) => setMfaCode(e.target.value)}
                        />
                        <button type="submit" disabled={isSubmitting}>
                            {isSubmitting ? "Enabling MFA…" : "Enable MFA and Sign In"}
                        </button>
                    </form>
                ) : mfaToken ? (
                    <form className="mfa-challenge-panel" onSubmit={handleMfaVerify} aria-busy={isSubmitting}>
                        <h2>MFA Verification</h2>
                        <p>Enter the six-digit code from your authenticator app.</p>

                        <input
                            type="text"
                            inputMode="numeric"
                            autoComplete="one-time-code"
                            aria-label="MFA verification code"
                            placeholder="MFA code"
                            value={mfaCode}
                            onChange={(e) => setMfaCode(e.target.value)}
                        />

                        <button type="submit" disabled={isSubmitting}>
                            {isSubmitting ? "Verifying…" : "Verify Code"}
                        </button>
                    </form>
                ) : !pendingToken ? (
                    <form onSubmit={handleSubmit} aria-busy={isSubmitting}>
                        <input
                            type="text"
                            aria-label="Username"
                            autoComplete="username"
                            placeholder="Username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                        />

                        <input
                            type="password"
                            aria-label="Password"
                            autoComplete="current-password"
                            placeholder="Password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />

                        <button type="submit" disabled={isSubmitting}>
                            {isSubmitting ? "Signing in…" : "Secure Login"}
                        </button>
                    </form>
                ) : (
                    <form className="password-change-panel" onSubmit={handlePasswordChange} aria-busy={isSubmitting}>
                        <h2>Password Update Required</h2>
                        <p>
                            Beacon requires a password change every 120 days.
                            Enter a new password before continuing.
                        </p>

                        <input
                            type="password"
                            aria-label="New password"
                            autoComplete="new-password"
                            placeholder="New password"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                        />

                        <input
                            type="password"
                            aria-label="Confirm new password"
                            autoComplete="new-password"
                            placeholder="Confirm new password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                        />

                        <button type="submit" disabled={isSubmitting}>
                            {isSubmitting ? "Updating password…" : "Update Password"}
                        </button>
                    </form>
                )}

                <div className="login-recovery-actions">
                    <button type="button" onClick={() => setRecoveryMode("password")}>
                        Forgot password
                    </button>
                    <button type="button" onClick={() => setRecoveryMode("username")}>
                        Forgot username
                    </button>
                </div>

                {recoveryMode && (
                    <div className="login-recovery-panel">
                        {recoveryMode === "password" ? (
                            <>
                                <h2>Forgot Password</h2>
                                <p>
                                    Contact your supervisor or Beacon administrator to verify
                                    your identity and issue a temporary password.
                                </p>
                            </>
                        ) : (
                            <>
                                <h2>Forgot Username</h2>
                                <p>
                                    Contact your supervisor or Beacon administrator with your
                                    agency email so your username can be verified.
                                </p>
                            </>
                        )}
                    </div>
                )}

                {error && <p className="error-text" role="alert">{error}</p>}
                {message && <p className="login-message">{message}</p>}
            </div>
        </div>
    );
}

export default Login;
