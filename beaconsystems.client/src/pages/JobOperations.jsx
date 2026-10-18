import React, { useEffect, useState } from "react";
import { apiGet, apiPost } from "../api.jsx";

const allowedRoles = ["platform_admin", "agency_admin", "supervisor"];

export default function JobOperations() {
    const allowed = allowedRoles.includes(localStorage.getItem("role"));
    const [metrics, setMetrics] = useState(null);
    const [loadedAt, setLoadedAt] = useState(null);
    const [jobs, setJobs] = useState([]);
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");
    const [busy, setBusy] = useState(false);
    const [reasons, setReasons] = useState({});

    async function refresh() {
        const [health, failed] = await Promise.all([
            apiGet("/operations/jobs/metrics"),
            apiGet("/operations/jobs/?status=dead_letter&limit=50"),
        ]);
        setMetrics(health);
        setJobs(failed);
        setLoadedAt(new Date());
    }

    useEffect(() => {
        if (!allowed) return;
        let active = true;
        Promise.all([
            apiGet("/operations/jobs/metrics"),
            apiGet("/operations/jobs/?status=dead_letter&limit=50"),
        ]).then(([health, failed]) => {
            if (active) { setMetrics(health); setJobs(failed); setLoadedAt(new Date()); }
        }).catch((err) => { if (active) setError(err.message); });
        return () => { active = false; };
    }, [allowed]);

    async function replay(event, jobId) {
        event.preventDefault();
        setBusy(true); setError(""); setMessage("");
        try {
            await apiPost(`/operations/jobs/${jobId}/replay`, { reason: reasons[jobId].trim() });
            setMessage(`Job ${jobId} queued for retry. The replay was recorded in the audit log.`);
            await refresh();
        } catch (err) { setError(err.message); }
        finally { setBusy(false); }
    }

    if (!allowed) return <div className="beacon-page"><h1>Operations</h1><p>Supervisor or administrator access is required.</p></div>;

    return <div className="beacon-page">
        <header className="beacon-page-header"><h1>Background operations</h1>
            <p>Queue health and jobs requiring attention for your authorized scope.</p>
            <button type="button" disabled={busy} onClick={async () => {
                setBusy(true); setError("");
                try { await refresh(); } catch (err) { setError(err.message); }
                finally { setBusy(false); }
            }}>Refresh operations</button>
        </header>
        {error && <p role="alert">{error}</p>}
        {message && <p role="status">{message}</p>}
        {!metrics && !error && <p role="status">Loading operations…</p>}
        {metrics && <section className="beacon-panel" aria-label="Queue health">
            <h2>Queue health: {metrics.status}</h2>
            <dl>
                <dt>Waiting jobs</dt><dd>{metrics.backlog}</dd>
                <dt>Dead-letter jobs</dt><dd>{metrics.dead_letters}</dd>
                <dt>Active workers</dt><dd>{metrics.active_workers}</dd>
                <dt>Oldest waiting job</dt><dd>{metrics.oldest_job_age_seconds} seconds</dd>
            </dl>
            <p>Last loaded: {loadedAt?.toLocaleTimeString()}. Refresh to check for changes.</p>
        </section>}
        <section className="beacon-panel"><h2>Failed jobs requiring review</h2>
            <p>Showing up to 50 recent dead-letter jobs. Correct the cause before replaying.</p>
            {metrics && jobs.length === 0 && <p>No dead-letter jobs found.</p>}
            {jobs.map((job) => <article key={job.job_id}>
                <h3>Job {job.job_id}: {job.job_type}</h3>
                <p>Attempts: {job.attempts} / {job.max_attempts}. Previous replays: {job.replay_count}.</p>
                <details><summary>Failure details</summary><pre>{job.last_error || "No failure details recorded."}</pre></details>
                <form onSubmit={(event) => replay(event, job.job_id)}>
                    <label htmlFor={`reason-${job.job_id}`}>Reason for replay</label>
                    <textarea id={`reason-${job.job_id}`} required minLength={5} maxLength={1000}
                        value={reasons[job.job_id] || ""}
                        onChange={(event) => setReasons({ ...reasons, [job.job_id]: event.target.value })} />
                    <button disabled={busy || (reasons[job.job_id] || "").trim().length < 5}>Replay job {job.job_id}</button>
                </form>
            </article>)}
        </section>
    </div>;
}
