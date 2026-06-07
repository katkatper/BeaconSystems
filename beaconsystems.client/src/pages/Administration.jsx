import React from "react";
import { Link } from "react-router-dom";

function Administration() {
    const administrationLinks = [
        ["Users", "/admin/users", "Manage accounts, roles, and supervisor access."],
        ["Audit", "/audit", "Review system activity, compliance logs, and user history."],
        ["Agencies", "/agencies", "Maintain agency registry and operational contacts."],
        ["Partners", "/partner-sources", "Approve external data sources and partner feeds."],
        ["Legal Orders", "/legal-orders", "Track warrants, subpoenas, and court orders."],
        ["Case Access", "/case-access", "Request or review restricted case access."],
    ];

    return (
        <div className="administration-page beacon-page">
            <section className="beacon-page-header">
                <h1>Administration</h1>
            </section>

            <section className="beacon-three-panel">
                {administrationLinks.map(([label, path, detail]) => (
                    <Link key={label} className="beacon-panel admin-link-card" to={path}>
                        <span>{label}</span>
                        <p>{detail}</p>
                    </Link>
                ))}
            </section>
        </div>
    );
}

export default Administration;
