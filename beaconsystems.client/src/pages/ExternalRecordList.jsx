import React, { useEffect, useMemo, useState } from "react";

function ExternalRecordList() {
    const [records, setRecords] = useState([]);
    const [partners, setPartners] = useState([]);
    const [sourceFilter, setSourceFilter] = useState("all");
    const [showMore, setShowMore] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem("token");
        const headers = {
            Authorization: `Bearer ${token}`,
        };

        Promise.all([
            fetch("http://127.0.0.1:8000/external-records/", { headers }),
            fetch("http://127.0.0.1:8000/integrations/", { headers }),
        ])
            .then(async ([recordsResponse, partnersResponse]) => {
                const recordsData = recordsResponse.ok
                    ? await recordsResponse.json()
                    : [];
                const partnersData = partnersResponse.ok
                    ? await partnersResponse.json()
                    : [];

                setRecords(Array.isArray(recordsData) ? recordsData : []);
                setPartners(Array.isArray(partnersData) ? partnersData : []);
            })
            .catch((err) => console.error(err));
    }, []);

    const partnersById = useMemo(() => {
        return partners.reduce((lookup, partner) => {
            lookup[partner.id] = partner;
            return lookup;
        }, {});
    }, [partners]);

    const filteredRecords = records.filter((record) => {
        const partner = partnersById[record.integration_source_id];

        if (sourceFilter === "all") return true;

        return partner?.source_type === sourceFilter;
    });

    const sourceTypes = [
        ...new Set(partners.map((partner) => partner.source_type).filter(Boolean)),
    ];

    return (
        <div className="external-records-page">
            <div className="external-records-header">
                <h1>External Records</h1>
            </div>

            <div className="external-records-toolbar">
                <label>
                    Source Type
                    <select
                        value={sourceFilter}
                        onChange={(e) => setSourceFilter(e.target.value)}
                    >
                        <option value="all">All sources</option>
                        {sourceTypes.map((type) => (
                            <option key={type} value={type}>
                                {type.replace("_", " ")}
                            </option>
                        ))}
                    </select>
                </label>
            </div>

            {filteredRecords.length === 0 ? (
                <div className="external-record-empty">
                    No external records match the current filter.
                </div>
            ) : (
                <div className="external-record-grid">
                    {filteredRecords.slice(0, showMore ? 6 : 2).map((record) => {
                        const partner = partnersById[record.integration_source_id];

                        return (
                            <article key={record.id} className="external-record-card">
                                <div className="external-record-topline">
                                    <strong>{record.record_type}</strong>
                                    <span
                                        className={`request-status ${
                                            partner?.status || "pending"
                                        }`}
                                    >
                                        {partner?.status || "unknown source"}
                                    </span>
                                </div>

                                <p>
                                    <strong>Partner:</strong>{" "}
                                    {partner?.name || "Unlinked partner"}
                                </p>
                                <p>
                                    <strong>Source:</strong>{" "}
                                    {partner?.source_type?.replace("_", " ") ||
                                        "unknown"}
                                </p>
                                <p>
                                    <strong>Case:</strong>{" "}
                                    {record.case_id ?? "unlinked"}
                                </p>
                                <p>
                                    <strong>Person:</strong>{" "}
                                    {record.person_id ?? "unlinked"}
                                </p>
                                <p>
                                    <strong>Name:</strong> {record.first_name}{" "}
                                    {record.last_name}
                                </p>
                                <p>
                                    <strong>Age:</strong> {record.age ?? "unknown"}
                                </p>
                                <p>
                                    <strong>Location:</strong>{" "}
                                    {record.location || "No location"}
                                </p>
                                <p>
                                    <strong>Notes:</strong>{" "}
                                    {record.notes || "No notes"}
                                </p>
                            </article>
                        );
                    })}
                    {filteredRecords.length > 2 && (
                        <button
                            type="button"
                            className="list-toggle-button"
                            onClick={() => setShowMore((current) => !current)}
                        >
                            {showMore ? "Show fewer" : `Show ${Math.min(4, filteredRecords.length - 2)} more records`}
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}

export default ExternalRecordList;
