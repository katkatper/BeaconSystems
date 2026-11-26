import { useState } from "react";
import { Link } from "react-router-dom";
import { apiUrl } from "../api.jsx";

export default function AccountOnboarding({ register = false }) {
    const [notice, setNotice] = useState("");
    const [error, setError] = useState("");
    const [busy, setBusy] = useState(false);

    async function submit(event) {
        event.preventDefault();
        if (busy || notice) return;
        const data = Object.fromEntries(new FormData(event.currentTarget));
        if (register) data.invitation_code = data.invitation_code.trim();
        setBusy(true);
        setError("");
        try {
            const path = register ? "/onboarding/register" : "/onboarding/access-requests";
            const response = await fetch(apiUrl(path), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(typeof result.detail === "string" ? result.detail : "Check the fields and try again.");
            }
            setNotice(result.message);
        } catch (err) {
            setError(err.message || "Could not reach Beacon. Try again.");
        } finally {
            setBusy(false);
        }
    }

    return (
        <section className="users-panel" style={{ maxWidth: "32rem", margin: "3rem auto" }}>
            <h1>{register ? "Create account" : "Request access"}</h1>
            <p>{register ? "Enter the code your Beacon administrator sent you."
                : "Send your work email and agency for review. A request does not grant access."}</p>
            {notice ? <p role="status">{notice}</p> : (
                <form className="supervisor-user-form" onSubmit={submit} aria-busy={busy}>
                    {register ? <>
                        <label>Invitation code<input name="invitation_code" required autoComplete="off" maxLength={80} /></label>
                        <label>Username<input name="username" required minLength={3} maxLength={64} pattern="[A-Za-z0-9_.\-]+" autoComplete="username" /></label>
                        <label>Password<input name="password" type="password" required minLength={12} maxLength={128} autoComplete="new-password" /></label>
                    </> : <>
                        <label>Work email<input name="email" type="email" required maxLength={254} autoComplete="email" /></label>
                        <label>Agency name<input name="agency_name" required minLength={2} maxLength={200} autoComplete="organization" /></label>
                    </>}
                    {error && <p role="alert">{error}</p>}
                    <button disabled={busy}>{busy ? "Submitting…" : register ? "Create account" : "Send request"}</button>
                </form>
            )}
            <p><Link to="/login">Back to sign in</Link></p>
        </section>
    );
}
