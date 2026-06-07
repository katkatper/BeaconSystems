import React, { useState } from "react";
import { useNavigate } from "react-router-dom";



function Login({ onLogin }) {

    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");
    const [recoveryMode, setRecoveryMode] = useState("");
    const [pendingToken, setPendingToken] = useState("");
    const navigate = useNavigate();

    const getLandingPath = (role) => {
        if (role === "agency_admin" || role === "supervisor") {
            return "/supervisor";
        }

        return "/";
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setMessage("");

        try {
            const response = await fetch("http://127.0.0.1:8000/users/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    username: username,
                    password: password,
                }),
            });

            if (!response.ok) {
                throw new Error("Login failed");
            }

            const data = await response.json();
            console.log("Login response:", data);

            localStorage.setItem("token", data.access_token);
            localStorage.setItem("role", data.role);
            localStorage.setItem("username", data.username);

            if (data.password_change_required) {
                setPendingToken(data.access_token);
                setMessage("Your password must be updated before continuing.");
                return;
            }

            if (onLogin) {
                onLogin(data.access_token);
            }

            navigate(getLandingPath(data.role));
        } catch (err) {
            console.error(err);
            setError("Invalid username or password");
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

        try {
            const response = await fetch("http://127.0.0.1:8000/users/change-password", {
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

            if (onLogin) {
                onLogin(pendingToken);
            }

            navigate(getLandingPath(localStorage.getItem("role")));
        } catch (err) {
            console.error(err);
            setError(err.message || "Could not update password");
        }
    };

    return (
        <div className="login-page">
            <div className="login-card">
                <h1>Beacon</h1>

                {!pendingToken ? (
                    <form onSubmit={handleSubmit}>
                        <input
                            type="text"
                            placeholder="Username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                        />

                        <input
                            type="password"
                            placeholder="Password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />

                        <button type="submit">
                            Secure Login
                        </button>
                    </form>
                ) : (
                    <form className="password-change-panel" onSubmit={handlePasswordChange}>
                        <h2>Password Update Required</h2>
                        <p>
                            Beacon requires a password change every 120 days.
                            Enter a new password before continuing.
                        </p>

                        <input
                            type="password"
                            placeholder="New password"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                        />

                        <input
                            type="password"
                            placeholder="Confirm new password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                        />

                        <button type="submit">
                            Update Password
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

                {error && <p className="error-text">{error}</p>}
                {message && <p className="login-message">{message}</p>}
            </div>
        </div>
    );
}

export default Login;
