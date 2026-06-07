import React, { useEffect, useState } from "react";

function Analytics() {
    const [summary, setSummary] = useState(null);

    useEffect(() => {
        let isMounted = true;
        const token = localStorage.getItem("token");

        fetch("http://127.0.0.1:8000/dashboard/summary", {
            headers: { Authorization: `Bearer ${token}` },
        })
            .then((response) => (response.ok ? response.json() : null))
            .then((data) => {
                if (isMounted) {
                    setSummary(data);
                }
            })
            .catch((err) => console.error(err));

        return () => {
            isMounted = false;
        };
    }, []);

    const metrics = [
        ["Open cases", summary?.open_cases ?? 42],
        ["Clearance rate", 68],
        ["Recovered", 17],
        ["Agency participation", 9],
        ["Investigator workload", 73],
        ["Case aging", 14],
    ];
    const maxValue = Math.max(...metrics.map(([, value]) => value), 1);

    return (
        <div className="analytics-page beacon-page">
            <section className="beacon-page-header">
                <h1>Analytics</h1>
            </section>

            <section className="beacon-three-panel analytics-grid">
                {metrics.map(([label, value]) => (
                    <article key={label} className="beacon-panel analytics-card">
                        <span>{label}</span>
                        <strong>{value}</strong>
                        <div className="analytics-bar" aria-hidden="true">
                            <span style={{ width: `${Math.max(12, (value / maxValue) * 100)}%` }} />
                        </div>
                    </article>
                ))}
            </section>
        </div>
    );
}

export default Analytics;
