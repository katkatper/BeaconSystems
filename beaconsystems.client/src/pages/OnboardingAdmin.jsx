import { useState } from "react";
import { apiGet, apiPost } from "../api.jsx";

export default function OnboardingAdmin({ platformAdmin }) {
    const [requests, setRequests] = useState([]);
    const [loaded, setLoaded] = useState(false);
    const [nextCursor, setNextCursor] = useState(null);
    const [busy, setBusy] = useState(false);
    const [notice, setNotice] = useState("");
    const [code, setCode] = useState("");

    async function run(action) {
        if (busy) return;
        setBusy(true);
        setNotice("");
        setCode("");
        try { await action(); }
        catch (error) { setNotice(error.message || "Could not complete the request."); }
        finally { setBusy(false); }
    }

    function submit(event) {
        event.preventDefault();
        const fields = Object.fromEntries(new FormData(event.currentTarget));
        const { request_id, email, role, agency_id } = fields;
        const assignment = { role, ...(agency_id ? { agency_id: Number(agency_id) } : {}) };
        run(async () => {
            const result = request_id
                ? await apiPost(`/onboarding/access-requests/${request_id}/decision`, { ...assignment, decision: "approve" })
                : await apiPost("/onboarding/invitations", { ...assignment, email });
            if (result.email_status === "sent") {
                setNotice("Invitation sent to the mail server.");
            } else {
                setCode(result.invitation_code);
                setNotice(result.email_status === "failed"
                    ? "Email delivery failed. Share the invitation code manually."
                    : "Email delivery is not configured. Share the invitation code manually.");
            }
            if (request_id) setRequests((items) => items.filter((item) => item.request_id !== Number(request_id)));
        });
    }

    function loadRequests(afterId = 0) {
        run(async () => {
            const page = await apiGet(`/onboarding/access-requests?after_id=${afterId}`);
            setRequests(page);
            setNextCursor(page.length === 50 ? page.at(-1).request_id : null);
            setLoaded(true);
        });
    }

    return (
        <section className="users-panel onboarding-admin-panel">
            <h2>Account invitations</h2>
            <p>Verify the recipient's identity and agency before sharing an invitation code through an approved channel.</p>
            {platformAdmin && <>
                <button type="button" disabled={busy} onClick={() => loadRequests()}>Load pending access requests</button>
                {nextCursor !== null && <button type="button" disabled={busy} onClick={() => loadRequests(nextCursor)}>Next requests</button>}
                {loaded && !requests.length && <p>No pending requests.</p>}
                {requests.map((item) => <div className="onboarding-request-row" key={item.request_id}>
                    <span>#{item.request_id} · {item.email} · {item.agency_name}</span>
                    <button type="button" disabled={busy} onClick={() => run(async () => {
                        await apiPost(`/onboarding/access-requests/${item.request_id}/decision`, { decision: "decline" });
                        setRequests((items) => items.filter((entry) => entry.request_id !== item.request_id));
                        setNotice("Request declined.");
                    })}>Decline request #{item.request_id}</button>
                </div>)}
            </>}
            <form className="supervisor-user-form" onSubmit={submit}>
                <label>Recipient work email (for a direct invitation)<input name="email" type="email" maxLength={254} /></label>
                {platformAdmin && <>
                    <label>Pending request ID (to approve instead)<input name="request_id" type="number" min={1} /></label>
                    <label>Verified agency ID<input name="agency_id" type="number" min={1} required /></label>
                </>}
                <label>Role<select name="role" defaultValue="viewer">
                    {["viewer", "investigator", "analyst", "supervisor"].map((role) => <option key={role}>{role}</option>)}
                </select></label>
                <button disabled={busy}>Issue invitation</button>
            </form>
            {notice && <p role="status">{notice}</p>}
            {code && <label>Single-use code (expires in 24 hours)<input readOnly value={code} /></label>}
        </section>
    );
}
