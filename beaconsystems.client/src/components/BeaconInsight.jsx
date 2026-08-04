import React, { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import { apiGet } from "../api.jsx";

const PAGE_LABELS = [
    [/^\/alerts/, "Alert context"],
    [/^\/cases\//, "Case context"],
    [/^\/cases|^\/missing/, "Investigation context"],
    [/^\/sightings|^\/escape-routes/, "Geographic context"],
    [/^\/intelligence|^\/analytics/, "Intelligence context"],
    [/^\/legal/, "Legal workflow context"],
    [/^\/bolos/, "BOLO context"],
    [/^\/evidence/, "Evidence context"],
    [/^\/partner|^\/agencies/, "Interagency context"],
    [/^\/supervisor|^\/$/, "Command context"],
];

function countLayers(summary) {
    return (summary?.operations_map?.locations || []).reduce((counts, item) => {
        const layer = item.layer || "other";
        counts[layer] = (counts[layer] || 0) + 1;
        return counts;
    }, {});
}

function buildInsights(pathname, summary) {
    if (!summary) return [];

    const layers = countLayers(summary);
    const insights = [];
    const recentSightings = summary.recent_sightings || [];
    const recentAlerts = summary.recent_alerts || [];

    if (pathname.startsWith("/alerts")) {
        const latest = recentAlerts[0];
        if (latest) {
            insights.push(`${latest.severity || "Active"} alert “${latest.title}” is the newest command-level alert in the current agency view.`);
        }
        insights.push(`${recentSightings.length} recent sighting${recentSightings.length === 1 ? " is" : "s are"} available for comparison across authorized investigations.`);
        insights.push(layers.hospital_inquiries
            ? `${layers.hospital_inquiries} open hospital inquir${layers.hospital_inquiries === 1 ? "y is" : "ies are"} represented on the operations map.`
            : "No open hospital inquiry is represented in the current operational area data.");
        insights.push(layers.interagency_requests
            ? `${layers.interagency_requests} interagency request${layers.interagency_requests === 1 ? " is" : "s are"} represented in the current operational view.`
            : "No active interagency request is represented in the current operational area data.");
    } else if (pathname.startsWith("/sightings") || pathname.startsWith("/escape-routes")) {
        insights.push(`${recentSightings.length} recent sighting${recentSightings.length === 1 ? " is" : "s are"} available in the authorized agency view.`);
        insights.push(`${layers.recent_sightings || 0} sighting location${layers.recent_sightings === 1 ? " is" : "s are"} currently mapped for geographic comparison.`);
        insights.push("Road, traffic-camera, and license-plate-reader proximity requires a connected local data source before Beacon can calculate it.");
    } else if (pathname.startsWith("/legal")) {
        insights.push(`${summary.pending_legal_requests || 0} legal order${summary.pending_legal_requests === 1 ? " is" : "s are"} pending.`);
        insights.push(`${summary.missing_info_legal_requests || 0} request${summary.missing_info_legal_requests === 1 ? " needs" : "s need"} additional information.`);
        insights.push(`${layers.hospital_inquiries || 0} open hospital inquir${layers.hospital_inquiries === 1 ? "y is" : "ies are"} represented geographically.`);
    } else if (pathname.startsWith("/intelligence") || pathname.startsWith("/analytics")) {
        insights.push(`${summary.high_risk_cases || 0} high-risk investigation${summary.high_risk_cases === 1 ? " is" : "s are"} active in the authorized view.`);
        insights.push(`${recentSightings.length} recent sighting${recentSightings.length === 1 ? " is" : "s are"} available for cross-case correlation.`);
        insights.push(`${(summary.operations_map?.locations || []).length} operational location${(summary.operations_map?.locations || []).length === 1 ? " is" : "s are"} available across connected map layers.`);
    } else if (pathname.startsWith("/bolos")) {
        insights.push(`${(summary.active_bolos || []).length} active BOLO${(summary.active_bolos || []).length === 1 ? " is" : "s are"} visible in the current agency scope.`);
        insights.push(`${layers.interagency_requests || 0} active interagency request${layers.interagency_requests === 1 ? " is" : "s are"} represented on the operations map.`);
        insights.push("Distribution and expiration should be reviewed before release; Beacon has not made an approval decision.");
    } else if (pathname.startsWith("/evidence")) {
        insights.push(`${summary.pending_evidence || 0} evidence item${summary.pending_evidence === 1 ? " is" : "s are"} pending review or processing.`);
        insights.push(`${summary.evidence_uploaded_today || 0} evidence item${summary.evidence_uploaded_today === 1 ? " was" : "s were"} uploaded today.`);
    } else if (pathname.startsWith("/partner") || pathname.startsWith("/agencies")) {
        insights.push(`${summary.agency_requests || 0} agency request${summary.agency_requests === 1 ? " is" : "s are"} active.`);
        insights.push(`${summary.pending_partner_sources || 0} partner source request${summary.pending_partner_sources === 1 ? " is" : "s are"} pending.`);
        insights.push(`${layers.interagency_requests || 0} interagency request${layers.interagency_requests === 1 ? " has" : "s have"} mapped location context.`);
    } else {
        insights.push(`${summary.open_cases || 0} active investigation${summary.open_cases === 1 ? " is" : "s are"} in the authorized agency view.`);
        insights.push(`${summary.critical_cases || 0} critical case${summary.critical_cases === 1 ? " requires" : "s require"} command visibility.`);
        insights.push(`${summary.outstanding_leads || 0} lead${summary.outstanding_leads === 1 ? " remains" : "s remain"} outstanding.`);
    }

    return insights.slice(0, 5);
}

function BeaconInsight() {
    const { pathname } = useLocation();
    const [summary, setSummary] = useState(null);
    const [error, setError] = useState("");
    const [collapsed, setCollapsed] = useState(false);
    const [updatedAt, setUpdatedAt] = useState(null);

    const loadInsights = () => {
        apiGet("/dashboard/summary")
            .then((data) => {
                setSummary(data);
                setError("");
                setUpdatedAt(new Date());
            })
            .catch(() => setError("Operational context is temporarily unavailable."));
    };

    useEffect(() => {
        loadInsights();
        const interval = window.setInterval(loadInsights, 60000);
        return () => window.clearInterval(interval);
    }, [pathname]);

    const contextLabel = PAGE_LABELS.find(([pattern]) => pattern.test(pathname))?.[1] || "Operational context";
    const insights = useMemo(() => buildInsights(pathname, summary), [pathname, summary]);

    return (
        <aside className={`beacon-insight-panel${collapsed ? " is-collapsed" : ""}`} aria-label="Beacon Insight">
            <button
                type="button"
                className="beacon-insight-toggle"
                onClick={() => setCollapsed((current) => !current)}
                aria-expanded={!collapsed}
            >
                <span className="beacon-insight-pulse" aria-hidden="true" />
                <strong>Beacon Insight</strong>
                <span>{collapsed ? "Open" : "Hide"}</span>
            </button>

            {!collapsed && (
                <div className="beacon-insight-body">
                    <div className="beacon-insight-heading">
                        <span>{contextLabel}</span>
                        <button type="button" onClick={loadInsights}>Refresh</button>
                    </div>

                    {error ? <p className="beacon-insight-error">{error}</p> : !summary ? (
                        <p>Reviewing authorized operational data…</p>
                    ) : (
                        <ul>
                            {insights.map((insight) => <li key={insight}>{insight}</li>)}
                        </ul>
                    )}

                    <footer>
                        <strong>Decision support only.</strong> Verify source records before action.
                        {updatedAt && <span> Updated {updatedAt.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}.</span>}
                    </footer>
                </div>
            )}
        </aside>
    );
}

export default BeaconInsight;
