import React, { useMemo, useState } from "react";
import SightingMap from "./SightingMap.jsx";
import { geocodeLocal } from "../geoUtils.js";

const directionProfiles = {
    unknown: {
        label: "Unknown direction",
        bearing: 0,
        routes: ["Nearest interstate access", "Major arterial grid", "Secondary rural connector"],
        factors: ["Direction not confirmed", "Prioritize converging routes", "Keep search area balanced"],
    },
    north: {
        label: "Northbound",
        bearing: 0,
        routes: ["Northbound interstate corridor", "Northern arterial feeder", "Airport or county-line route"],
        factors: ["Witness direction favors north", "Fastest movement toward regional exits", "Multiple feeder streets converge northbound"],
    },
    south: {
        label: "Southbound",
        bearing: 180,
        routes: ["Southbound interstate corridor", "Southern arterial feeder", "Industrial or port access route"],
        factors: ["Witness direction favors south", "Direct route away from origin", "Limited-access roads become priority"],
    },
    east: {
        label: "Eastbound",
        bearing: 90,
        routes: ["Eastbound highway corridor", "Eastern arterial feeder", "Bridge or river-crossing route"],
        factors: ["Witness direction favors east", "Likely connection to major highway", "Check crossings and interchanges"],
    },
    west: {
        label: "Westbound",
        bearing: 270,
        routes: ["Westbound highway corridor", "Western arterial feeder", "Outer-loop connector"],
        factors: ["Witness direction favors west", "Likely escape toward outer-loop access", "Surface routes may avoid cameras"],
    },
};

const vehicleProfiles = {
    passenger: { label: "Passenger vehicle", speed: 42, confidence: 12 },
    suv: { label: "SUV / truck", speed: 40, confidence: 10 },
    motorcycle: { label: "Motorcycle", speed: 46, confidence: 8 },
    commercial: { label: "Commercial vehicle", speed: 34, confidence: -2 },
    rideshare: { label: "Rideshare / taxi", speed: 38, confidence: 5 },
    on_foot: { label: "On foot", speed: 3, confidence: -10 },
    unknown: { label: "Unknown", speed: 30, confidence: 0 },
};

const radiusBands = [5, 10, 20, 30, 60];

const initialForm = {
    abductionLocation: "",
    incidentTime: "",
    currentTime: "",
    direction: "unknown",
    travelMode: "passenger",
    vehicleDescription: "",
    licensePlate: "",
    occupants: "",
    witnessStatement: "",
    knownSightings: "",
    roadContext: "urban",
};

const roadContextProfiles = {
    urban: { label: "Urban", multiplier: 0.82, factors: ["Traffic signals", "Camera coverage", "Multiple route choices"] },
    suburban: { label: "Suburban", multiplier: 0.95, factors: ["Arterial access", "Interstate feeders", "Mixed residential roads"] },
    rural: { label: "Rural", multiplier: 1.08, factors: ["Longer uninterrupted travel", "Fewer cameras", "County roads"] },
    highway: { label: "Near limited-access highway", multiplier: 1.22, factors: ["Rapid highway access", "Fewer exit points", "Choke points become critical"] },
};

function minutesSinceIncident(form) {
    if (!form.incidentTime || !form.currentTime) return 20;

    const incident = new Date(form.incidentTime);
    const current = new Date(form.currentTime);
    const diff = Math.round((current.getTime() - incident.getTime()) / 60000);

    if (!Number.isFinite(diff) || diff <= 0) return 20;
    return Math.min(diff, 240);
}

function scoreRoute(index, form, elapsedMinutes) {
    const directionScore = form.direction === "unknown" ? 12 : 26;
    const plateScore = form.licensePlate.trim() ? 12 : 0;
    const sightingScore = form.knownSightings.trim() ? 18 : 0;
    const witnessScore = form.witnessStatement.trim() ? 10 : 0;
    const elapsedScore = elapsedMinutes <= 20 ? 18 : elapsedMinutes <= 60 ? 10 : 4;
    const base = 42 - index * 13;
    return Math.max(18, Math.min(96, base + directionScore + plateScore + sightingScore + witnessScore + elapsedScore));
}

function getRouteSummary(route, likelihood, form) {
    const vehicleContext = vehicleProfiles[form.travelMode]?.label || "Unknown vehicle";
    const routeTone = likelihood === "Higher"
        ? "Primary corridor for immediate review"
        : likelihood === "Moderate"
            ? "Secondary corridor to monitor"
            : "Lower-priority route unless new information supports it";

    return `${routeTone}. ${vehicleContext}; ${directionProfiles[form.direction]?.label || "direction unknown"}.`;
}

function getRouteAction(likelihood) {
    if (likelihood === "Higher") {
        return "Check cameras, LPRs, and patrol availability first.";
    }

    if (likelihood === "Moderate") {
        return "Hold for follow-up if sightings, plate hits, or witness updates support this path.";
    }

    return "Keep visible for context; avoid overcommitting resources without more support.";
}

function EscapeRouteAnalysis({ embedded = false, caseContext = null, onAnalysisRun = null, onTimelineEventSaved = null }) {
    const [form, setForm] = useState({
        ...initialForm,
        abductionLocation: caseContext?.lastSeenLocation || "",
    });
    const [analysisStarted, setAnalysisStarted] = useState(false);
    const [submittedAnalysis, setSubmittedAnalysis] = useState(null);
    const [saveStatus, setSaveStatus] = useState("");
    const [isSaving, setIsSaving] = useState(false);

    const analysis = useMemo(() => {
        const elapsedMinutes = minutesSinceIncident(form);
        const vehicle = vehicleProfiles[form.travelMode] || vehicleProfiles.unknown;
        const roadContext = roadContextProfiles[form.roadContext] || roadContextProfiles.urban;
        const adjustedSpeed = vehicle.speed * roadContext.multiplier;
        const direction = directionProfiles[form.direction] || directionProfiles.unknown;

        const reachableBands = radiusBands.map((minutes) => ({
            minutes,
            miles: Math.max(0.3, Number(((adjustedSpeed * minutes) / 60).toFixed(1))),
            active: minutes <= elapsedMinutes,
        }));

        const likelyRoutes = direction.routes.map((route, index) => {
            const score = scoreRoute(index, form, elapsedMinutes);
            const likelihood = score >= 76 ? "Higher" : score >= 52 ? "Moderate" : "Lower";

            return {
                route,
                score,
                likelihood,
                summary: getRouteSummary(route, likelihood, form),
                recommendedAction: getRouteAction(likelihood),
                factors: [
                    direction.factors[index] || direction.factors[0],
                    roadContext.factors[index] || roadContext.factors[0],
                    form.knownSightings.trim() ? "New sighting narrows the corridor" : "Awaiting confirmed sightings",
                ],
            };
        });

        const chokePoints = [
            {
                name: "Closest limited-access highway entrances",
                priority: form.roadContext === "highway" ? "Immediate" : "High",
                reason: "Fastest transition from local streets to regional travel.",
            },
            {
                name: "Major arterial intersections leaving the origin area",
                priority: "High",
                reason: "Multiple plausible paths converge before spreading outward.",
            },
            {
                name: "Bridges, toll plazas, ferries, or controlled crossings",
                priority: form.direction === "unknown" ? "Medium" : "High",
                reason: "Traffic naturally funnels through constrained access points.",
            },
            {
                name: "Interstate interchanges inside the active travel band",
                priority: elapsedMinutes <= 30 ? "High" : "Medium",
                reason: "A suspect can change direction quickly once on a highway network.",
            },
        ];

        const resourceSuggestions = [
            "Confirm witness direction, vehicle identifiers, and last known travel lane.",
            "Check traffic cameras, license plate readers, and nearby business CCTV along higher-probability corridors.",
            "Notify partner agencies positioned near highway entrances and major crossings.",
            "Update the analysis after each sighting, LPR hit, or confirmed road closure.",
        ];

        const recommendedAttentionAreas = [
            {
                label: "First 20-minute travel band",
                priority: elapsedMinutes <= 20 ? "Immediate" : "Review",
                detail: "Focus on routes the suspect could plausibly reach before leaving the initial response area.",
            },
            {
                label: direction.routes[0],
                priority: likelyRoutes[0]?.likelihood || "Moderate",
                detail: likelyRoutes[0]?.recommendedAction || "Review available route intelligence.",
            },
            {
                label: "Transportation choke points",
                priority: form.direction === "unknown" ? "High" : "Immediate",
                detail: "Prioritize highway entrances, interchanges, bridges, toll plazas, and constrained crossings.",
            },
            {
                label: "New incoming observations",
                priority: form.knownSightings.trim() ? "Immediate" : "Pending",
                detail: form.knownSightings.trim()
                    ? "Use the new sighting/context notes to update likely corridors."
                    : "Add sightings, LPR hits, CCTV detections, closures, or weather to refine the analysis.",
            },
        ];

        return {
            elapsedMinutes,
            vehicle,
            roadContext,
            direction,
            directionKey: form.direction,
            reachableBands,
            likelyRoutes,
            chokePoints,
            recommendedAttentionAreas,
            resourceSuggestions,
        };
    }, [form]);

    const handleChange = (event) => {
        const { name, value } = event.target;
        setForm((current) => ({ ...current, [name]: value }));
    };

    const clearField = (fieldName) => {
        setForm((current) => ({ ...current, [fieldName]: "" }));
        setSaveStatus("");
    };

    const geocodeAnalysisOrigin = async (value) => {
        const token = localStorage.getItem("token");

        if (token && value.trim()) {
            try {
                const response = await fetch(
                    `http://127.0.0.1:8000/geocoding/address?address=${encodeURIComponent(value)}`,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );

                if (response.ok) {
                    return response.json();
                }
            } catch (error) {
                console.error(error);
            }
        }

        return geocodeLocal(value);
    };

    const clearAllFields = () => {
        setForm(initialForm);
        setAnalysisStarted(false);
        setSubmittedAnalysis(null);
        setSaveStatus("");
        onAnalysisRun?.(null);
    };

    const renderClearableField = (fieldName, field) => (
        <div className="escape-clearable-field">
            {field}
            {form[fieldName] && (
                <button
                    type="button"
                    className="escape-field-clear"
                    onClick={() => clearField(fieldName)}
                >
                    Clear
                </button>
            )}
        </div>
    );

    const handleSubmit = async (event) => {
        event.preventDefault();
        const geocodedOrigin = await geocodeAnalysisOrigin(form.abductionLocation);
        const nextAnalysis = {
            ...analysis,
            generatedAt: new Date().toISOString(),
            origin: geocodedOrigin
                ? {
                    ...geocodedOrigin,
                    label: "Incident Origin",
                    address: form.abductionLocation,
                }
                : null,
        };

        setAnalysisStarted(true);
        setSubmittedAnalysis(nextAnalysis);
        setSaveStatus("");
        onAnalysisRun?.(nextAnalysis);
    };

    const buildTimelineDescription = () => {
        const topRoute = renderedAnalysis.likelyRoutes[0];
        const activeBand = renderedAnalysis.reachableBands
            .filter((band) => band.active)
            .at(-1);

        return [
            `Escape Route Analysis generated for ${caseContext?.caseNumber || "case"}.`,
            `Incident origin: ${form.abductionLocation || "not recorded"}.`,
            `Elapsed time estimate: ${renderedAnalysis.elapsedMinutes} minutes.`,
            activeBand ? `Active travel band: ${activeBand.minutes} minutes / ${activeBand.miles} miles.` : null,
            topRoute ? `Top route: ${topRoute.route} (${topRoute.likelihood}, ${topRoute.score}%).` : null,
            topRoute ? `Recommended action: ${topRoute.recommendedAction}` : null,
        ].filter(Boolean).join(" ");
    };

    const saveAnalysisToTimeline = async () => {
        if (!submittedAnalysis || !caseContext?.caseId) {
            setSaveStatus("Run the analysis before saving it to the timeline.");
            return;
        }

        setIsSaving(true);
        setSaveStatus("");

        try {
            const token = localStorage.getItem("token");
            const response = await fetch("http://127.0.0.1:8000/timeline-events/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    case_id: caseContext.caseId,
                    person_id: caseContext.personId || null,
                    event_type: "escape_route_analysis",
                    source_type: "beacon_escape_route",
                    location: form.abductionLocation || null,
                    description: buildTimelineDescription(),
                }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Could not save analysis to timeline.");
            }

            const savedEvent = await response.json();
            onTimelineEventSaved?.(savedEvent);
            setSaveStatus("Escape route analysis saved to the case timeline.");
        } catch (error) {
            console.error(error);
            setSaveStatus(error.message || "Could not save analysis to timeline.");
        } finally {
            setIsSaving(false);
        }
    };

    const draftOrigin = geocodeLocal(form.abductionLocation);
    const displayedAnalysis = submittedAnalysis || (analysisStarted ? analysis : null);
    const renderedAnalysis = displayedAnalysis || analysis;
    const displayedOrigin = displayedAnalysis?.origin || (
        draftOrigin
            ? {
                ...draftOrigin,
                label: "Incident Origin",
                address: form.abductionLocation,
            }
            : null
    );

    return (
        <div className={embedded ? "escape-route-page escape-route-embedded" : "escape-route-page beacon-page"}>
            {!embedded && (
                <section className="beacon-page-header">
                    <h1>Escape Route Analysis</h1>
                </section>
            )}

            {embedded && caseContext && (
                <div className="audit-panel-heading escape-route-case-heading">
                    <span>Case Tool</span>
                    <strong>Escape Route Analysis for {caseContext.caseNumber}</strong>
                </div>
            )}

            <section className="escape-route-layout">
                <form className="beacon-panel escape-route-form" onSubmit={handleSubmit}>
                    <div className="audit-panel-heading">
                        <span>Investigator Input</span>
                        <strong>Incident facts</strong>
                    </div>

                    <div className="escape-form-grid">
                        {renderClearableField("abductionLocation", (
                            <input
                                name="abductionLocation"
                                value={form.abductionLocation}
                                onChange={handleChange}
                                placeholder="Abduction location"
                            />
                        ))}
                        {renderClearableField("incidentTime", (
                            <input
                                name="incidentTime"
                                type="datetime-local"
                                value={form.incidentTime}
                                onChange={handleChange}
                                aria-label="Incident time"
                            />
                        ))}
                        {renderClearableField("currentTime", (
                            <input
                                name="currentTime"
                                type="datetime-local"
                                value={form.currentTime}
                                onChange={handleChange}
                                aria-label="Current analysis time"
                            />
                        ))}
                        <select name="direction" value={form.direction} onChange={handleChange}>
                            <option value="unknown">Direction unknown</option>
                            <option value="north">Northbound</option>
                            <option value="south">Southbound</option>
                            <option value="east">Eastbound</option>
                            <option value="west">Westbound</option>
                        </select>
                        <select name="travelMode" value={form.travelMode} onChange={handleChange}>
                            {Object.entries(vehicleProfiles).map(([value, profile]) => (
                                <option value={value} key={value}>{profile.label}</option>
                            ))}
                        </select>
                        <select name="roadContext" value={form.roadContext} onChange={handleChange}>
                            {Object.entries(roadContextProfiles).map(([value, profile]) => (
                                <option value={value} key={value}>{profile.label}</option>
                            ))}
                        </select>
                        {renderClearableField("vehicleDescription", (
                            <input
                                name="vehicleDescription"
                                value={form.vehicleDescription}
                                onChange={handleChange}
                                placeholder="Vehicle description"
                            />
                        ))}
                        {renderClearableField("licensePlate", (
                            <input
                                name="licensePlate"
                                value={form.licensePlate}
                                onChange={handleChange}
                                placeholder="License plate"
                            />
                        ))}
                        {renderClearableField("occupants", (
                            <input
                                name="occupants"
                                value={form.occupants}
                                onChange={handleChange}
                                placeholder="Number of occupants"
                            />
                        ))}
                        {renderClearableField("witnessStatement", (
                            <textarea
                                name="witnessStatement"
                                value={form.witnessStatement}
                                onChange={handleChange}
                                placeholder="Witness statements"
                            />
                        ))}
                        {renderClearableField("knownSightings", (
                            <textarea
                                name="knownSightings"
                                value={form.knownSightings}
                                onChange={handleChange}
                                placeholder="New sightings, LPR hits, CCTV detections, road closures, or weather context"
                            />
                        ))}
                    </div>

                    <div className="escape-form-actions">
                        <button type="submit">Run Escape Route Analysis</button>
                        <button type="button" onClick={clearAllFields}>Clear All Fields</button>
                    </div>
                </form>

                <section className={`beacon-panel escape-route-map-panel ${displayedAnalysis ? "analysis-active" : ""}`}>
                    <div className="audit-panel-heading">
                        <span>Unified Case Geography</span>
                        <strong>Sightings, route bands, and associate addresses</strong>
                    </div>

                    <SightingMap
                        sightings={caseContext?.sightings || []}
                        associateLocations={caseContext?.associateLocations || []}
                        mappedLocations={caseContext?.mappedLocations || []}
                        escapeAnalysis={displayedAnalysis}
                        analysisOrigin={displayedOrigin}
                    />

                    <div className="escape-radius-list">
                        {renderedAnalysis.reachableBands.map((band) => (
                            <div key={band.minutes} className={band.active ? "active" : ""}>
                                <span>{band.minutes} minutes</span>
                                <strong>{band.miles} mi</strong>
                            </div>
                        ))}
                    </div>

                    {displayedAnalysis && (
                        <div className="escape-map-status">
                            <strong>Analysis overlays active</strong>
                            <span>{renderedAnalysis.direction.label} | {renderedAnalysis.elapsedMinutes} minute elapsed estimate</span>
                        </div>
                    )}
                </section>
            </section>

            <section className="escape-analysis-grid">
                <div className="beacon-panel route-ranking-panel">
                    <div className="audit-panel-heading">
                        <span>Dynamic Probability Scoring</span>
                        <strong>Likely routes</strong>
                    </div>
                    {renderedAnalysis.likelyRoutes.map((route) => (
                        <article className="route-score-card" key={route.route}>
                            <div>
                                <h2>{route.route}</h2>
                                <span>{route.likelihood} | {route.score}%</span>
                            </div>
                            <meter min="0" max="100" value={route.score}>{route.score}</meter>
                            <strong>{route.summary}</strong>
                            <p>{route.factors.join(" | ")}</p>
                            <small>{route.recommendedAction}</small>
                        </article>
                    ))}
                </div>

                <div className="beacon-panel choke-point-panel">
                    <div className="audit-panel-heading">
                        <span>Road Network Analysis</span>
                        <strong>Priority choke points</strong>
                    </div>
                    {renderedAnalysis.chokePoints.map((point) => (
                        <article className="choke-point-card" key={point.name}>
                            <span>{point.priority}</span>
                            <strong>{point.name}</strong>
                            <p>{point.reason}</p>
                        </article>
                    ))}
                </div>

                <div className="beacon-panel resource-allocation-panel">
                    <div className="audit-panel-heading">
                        <span>Resource Allocation</span>
                        <strong>Recommended attention areas</strong>
                    </div>
                    {renderedAnalysis.recommendedAttentionAreas.map((area) => (
                        <article className="attention-area-card" key={area.label}>
                            <span>{area.priority}</span>
                            <strong>{area.label}</strong>
                            <p>{area.detail}</p>
                        </article>
                    ))}
                    {renderedAnalysis.resourceSuggestions.map((suggestion) => (
                        <p key={suggestion} className="resource-followup">{suggestion}</p>
                    ))}
                </div>

                <div className="beacon-panel transparency-panel">
                    <div className="audit-panel-heading">
                        <span>Transparency</span>
                        <strong>Decision support only</strong>
                    </div>
                    <p>
                        Beacon ranks plausible movement corridors from entered facts, time elapsed,
                        travel mode, and road context. It does not confirm suspect location or replace
                        investigator judgment.
                    </p>
                    <div className="beacon-status-list">
                        <span>Vehicle model: {renderedAnalysis.vehicle.label}</span>
                        <span>Road context: {renderedAnalysis.roadContext.label}</span>
                        <span>Analysis status: {displayedAnalysis ? "Generated" : "Ready for input"}</span>
                    </div>
                    {embedded && (
                        <div className="escape-timeline-save">
                            <button
                                type="button"
                                onClick={saveAnalysisToTimeline}
                                disabled={!submittedAnalysis || isSaving}
                            >
                                {isSaving ? "Saving Analysis" : "Save Analysis to Timeline"}
                            </button>
                            {saveStatus && <p>{saveStatus}</p>}
                        </div>
                    )}
                </div>
            </section>
        </div>
    );
}

export default EscapeRouteAnalysis;
