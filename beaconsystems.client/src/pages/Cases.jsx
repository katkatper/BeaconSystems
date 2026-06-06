import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const fetchCases = async (includeArchived) => {
    const token = localStorage.getItem("token");

    const response = await fetch(
        `http://127.0.0.1:8000/cases/?include_archived=${includeArchived}&limit=100`,
        {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        }
    );

    if (!response.ok) {
        throw new Error("Failed to load cases");
    }

    return response.json();
};

function Cases() {
    const [cases, setCases] = useState([]);
    const [includeArchived, setIncludeArchived] = useState(false);
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

    const openCases = cases.filter((caseItem) => {
        const status = (caseItem.case_status || "").toLowerCase();
        return status !== "closed" && status !== "archived";
    });

    const closedCases = cases.filter((caseItem) => {
        const status = (caseItem.case_status || "").toLowerCase();
        return status === "closed" || status === "archived";
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

            <div className="case-summary-sections">
                <section className="case-summary-panel">
                    <div className="case-summary-title">
                        <h2>Open Cases</h2>
                        <span>{openCases.length}</span>
                    </div>
                    {renderCaseRows(openCases, "No open cases available.")}
                </section>

                <section className="case-summary-panel">
                    <div className="case-summary-title">
                        <h2>Closed Cases</h2>
                        <div className="closed-case-controls">
                            <label className="archive-toggle">
                                <input
                                    type="checkbox"
                                    checked={includeArchived}
                                    onChange={(e) => setIncludeArchived(e.target.checked)}
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
