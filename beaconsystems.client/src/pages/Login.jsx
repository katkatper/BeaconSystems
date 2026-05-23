import React, { useState } from "react";
import { useNavigate } from "react-router-dom";



function Login({ onLogin }) {

    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");

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

            navigate("/");

            if (onLogin) {
                onLogin(data.access_token);
            }

            navigate("/");
        } catch (err) {
            console.error(err);
            setError("Invalid username or password");
        }
    };

    return (
        <div className="login-page">
            <div className="login-card">
                <h1>Beacon</h1>

                <p className="login-subtitle">
                    Investigative Intelligence Platform
                </p>

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

                {error && <p className="error-text">{error}</p>}
            </div>
        </div>
    );
}

export default Login;