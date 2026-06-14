import React, { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { apiGet } from "../api.jsx";
import ActiveFilterBanner from "../components/ActiveFilterBanner.jsx";

const fetchCases = async (includeArchived) => {
    return apiGet(`/cases/?include_archived=${includeArchived}&limit=100`);
};

function Cases() {
    const [searchParams, setSearchParams] = useSearchParams();
    const activeFilter = searchParams.get("filter") || "all";
    const includeArchived = activeFilter === "archived";
    const [referenceNow] = useState(() => Date.now());
    const [cases, setCases] = useState([]);
    const [message, setMessage] = useState("");

    useEffect(() => {
        let isMounted = true;

        fetchCases(includeArchived)
            .then((data) => {
                if (!isMounted) {
                    return;
                }

                setCases(Array.isArray(data) ? data : []);
                setMessage("");
            })
            .catch((err) => {
                console.error(err);

                if (isMounted) {
                    setMessage("Could not load cases.");
                }
            });

        return () => {
            isMounted = false;
        };
    }, [includeArchived]);

    const isInactive = (caseItem) => {
        const lastUpdated = new Date(caseItem.updated_at || caseItem.created_at);

        if (Number.isNaN(lastUpdated.getTime())) {
            return false;
        }

        const ageInDays = (referenceNow - lastUpdated.getTime()) / (1000 * 60 * 60 * 24);
        return ageInDays >= 7;
    };

    const filterLabels = {
        all: "All active cases",
        stalled: "Investigations at risk of stalling",
        unassigned: "Unassigned cases",
        high_risk: "High-risk cases",
        missing_reports: "Cases missing reports",
        archived: "Archived and closed cases",
    };

    const openCases = cases.filter((caseItem) => {
        const status = (caseItem.case_status || "").toLowerCase();
        return status !== "closed" && status !== "archived";
    });

    const closedCases = cases.filter((caseItem) => {
        const status = (caseItem.case_status || "").toLowerCase();
        return status === "closed" || status === "archived";
    });

    const filteredOpenCases = openCases.filter((caseItem) => {
        const priority = (caseItem.priority_level || "").toLowerCase();

        if (activeFilter === "stalled") {
            return isInactive(caseItem);
        }

        if (activeFilter === "unassigned") {
            return !caseItem.investigator_id;
        }

        if (activeFilter === "high_risk") {
            return priority === "high" || priority === "critical";
        }

        if (activeFilter === "missing_reports") {
            return isInactive(caseItem);
        }

        return true;
    });

    const renderCaseRows = (items, emptyMessage) => {
        if (items.length === 0) {
            return <p>{emptyMessage}</p>;
        }

        return (
            <div className="case-summary-list">
                <div className="case-summary-row case-summary-heading">
                    <span>Case Number</span>
                    <span>Missing Person</span>
                    <span>Investigator</span>
                </div>

                {[...items]
                    .sort((firstCase, secondCase) =>
                        (firstCase.case_number || "").localeCompare(secondCase.case_number || "")
                    )
                    .map((caseItem) => (
                    <div key={caseItem.case_id} className="case-summary-row">
                        <Link to={`/cases/${caseItem.case_id}`}>
                            {caseItem.case_number || `Case ${caseItem.case_id}`}
                        </Link>
                        <span>{caseItem.missing_person_last_name || "Unknown"}</span>
                        <span>
                            {caseItem.investigator_name ||
                                (caseItem.investigator_id
                                    ? `Investigator ${caseItem.investigator_id}`
                                    : "Unassigned")}
                        </span>
                    </div>
                ))}
            </div>
        );
    };

    return (
        <div className="cases-page">
            <div className="cases-header">
                <div>
                    <h1>Cases</h1>
                </div>
            </div>

            {message && <p className="alert-banner">{message}</p>}

            {activeFilter !== "all" && (
                <ActiveFilterBanner onClear={() => setSearchParams({})}>
                    {filterLabels[activeFilter] || "Filtered case queue"}
                </ActiveFilterBanner>
            )}

            <div className="case-summary-sections">
                <section className="case-summary-panel">
                    <div className="case-summary-title">
                        <h2>Open Cases</h2>
                        <span>{filteredOpenCases.length}</span>
                    </div>
                    {renderCaseRows(filteredOpenCases, "No cases match this queue.")}
                </section>

                <section className="case-summary-panel">
                    <div className="case-summary-title">
                        <h2>Closed Cases</h2>
                        <div className="closed-case-controls">
                            <label className="archive-toggle">
                                <input
                                    type="checkbox"
                                    checked={includeArchived}
                                    onChange={(e) => {
                                        const checked = e.target.checked;
                                        setSearchParams(checked ? { filter: "archived" } : {});
                                    }}
                                />
                                Show archived
                            </label>
                            <span>{closedCases.length}</span>
                        </div>
                    </div>
                    {renderCaseRows(closedCases, "No closed cases available.")}
                </section>
            </div>
        </div>
    );
}

export default Cases;
