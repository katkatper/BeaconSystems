import React, { useMemo, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";

const globalSearchTargets = [
    ["Cases", "/cases", "case number, status, assigned investigator"],
    ["Persons", "/missing", "name, demographics, last seen location"],
    ["Evidence", "/evidence-upload", "evidence ID, type, status, location"],
    ["Leads", "/intelligence", "tips, matches, external intelligence"],
    ["Alerts", "/alerts", "BOLOs, critical alerts, escalation notices"],
    ["Agencies", "/agencies", "partner agencies and resource contacts"],
];

function Navbar() {
    const navigate = useNavigate();
    const [collapsed, setCollapsed] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");
    const role = localStorage.getItem("role");
    const username = localStorage.getItem("username") || "Beacon User";
    const navigation = [
        ["Dashboard", "/", "D"],
        ["Missing Persons", "/missing", "M"],
        ["Cases", "/cases", "C"],
        ["Intelligence", "/intelligence", "I"],
        ["Sightings", "/sightings", "S"],
        ["Evidence", "/evidence-upload", "E"],
        ["Alerts", "/alerts", "A"],
        ["Agencies", "/agencies", "A"],
        ["Analytics", "/analytics", "A"],
        ["Partners", "/partner-sources", "P"],
        ["Users", "/admin/users", "U"],
        ["Administration", "/administration", "A"],
    ];
    const navLinks = {
        admin: navigation,
        agency_admin: navigation,
        supervisor: navigation,
        investigator: navigation.filter(([label]) =>
            ["Dashboard", "Missing Persons", "Cases", "Intelligence", "Sightings", "Evidence", "Alerts"].includes(label)
        ),
        analyst: navigation.filter(([label]) =>
            ["Dashboard", "Cases", "Intelligence", "Sightings", "Evidence", "Alerts", "Analytics"].includes(label)
        ),
        viewer: navigation.filter(([label]) =>
            ["Dashboard", "Missing Persons", "Cases"].includes(label)
        ),
    };
    const roleLabels = {
        admin: "Administrator",
        agency_admin: "Supervisor",
        supervisor: "Supervisor",
        investigator: "Detective",
        analyst: "Analyst",
        viewer: "Viewer",
    };
    const displayRole = roleLabels[role] || "Team Member";
    const visibleLinks = navLinks[role] || navLinks.viewer;
    const searchResults = useMemo(() => {
        const normalized = searchTerm.trim().toLowerCase();

        if (!normalized) {
            return globalSearchTargets;
        }

        return globalSearchTargets.filter(([label, , detail]) =>
            `${label} ${detail}`.toLowerCase().includes(normalized)
        );
    }, [searchTerm]);

    const handleLogout = () => {
        localStorage.clear();
        navigate("/login");
    };

    const handleSearch = (e) => {
        e.preventDefault();
        const firstResult = searchResults[0];

        if (firstResult) {
            navigate(firstResult[1]);
        }
    };

    const handlePanelClick = (event) => {
        if (event.target.closest("a, button, input, select, textarea")) return;

        setCollapsed((current) => !current);
    };

    return (
        <>
            <nav
                className={`navbar ${collapsed ? "navbar-collapsed" : ""}`}
                onClick={handlePanelClick}
                title="Click empty sidebar space to collapse or expand"
            >
                <div className="navbar-topline">
                    <div className="navbar-brand-row">
                        <Link className="navbar-brand" to="/" aria-label="Go to Beacon dashboard">
                            <div className="brand-mark" aria-hidden="true">
                                <span className="brand-ray brand-ray-main"></span>
                                <span className="brand-ray brand-ray-soft"></span>
                                <span className="brand-ray brand-ray-side"></span>
                            </div>
                            <div>
                                <h2>Beacon</h2>
                                <span>Recovery Intelligence Platform</span>
                            </div>
                        </Link>
                    </div>

                    <div className="navbar-welcome">
                        <span>Welcome back</span>
                        <strong>{displayRole} {username}</strong>
                    </div>
                </div>

                <div className="navbar-links">
                    {visibleLinks.map(([label, path, initial]) => (
                        <NavLink key={path} to={path}>
                            <span className="nav-initial" aria-hidden="true">{initial}</span>
                            <span className="nav-label">{label}</span>
                        </NavLink>
                    ))}
                </div>
            </nav>

            <header className={`top-command-header ${collapsed ? "sidebar-collapsed" : ""}`}>
                <form className="global-search" onSubmit={handleSearch}>
                    <input
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="Search Anything..."
                        aria-label="Search cases, persons, evidence, leads, alerts, and agencies"
                    />
                    {searchTerm && (
                        <div className="global-search-results">
                            {searchResults.length === 0 ? (
                                <span>No matching Beacon area found.</span>
                            ) : (
                                searchResults.slice(0, 6).map(([label, path, detail]) => (
                                    <button
                                        type="button"
                                        key={label}
                                        onClick={() => {
                                            setSearchTerm("");
                                            navigate(path);
                                        }}
                                    >
                                        <strong>{label}</strong>
                                        <small>{detail}</small>
                                    </button>
                                ))
                            )}
                        </div>
                    )}
                </form>

                <div className="top-header-actions" aria-label="Command tools">
                    <Link to="/command/notifications">Notifications</Link>
                <Link to="/command/tasks">Tasks</Link>
                <Link to="/command/settings">Settings</Link>
                <Link to="/command/profile">Profile</Link>
                <button type="button" onClick={handleLogout}>Logout</button>
            </div>
            </header>
        </>
    );
}

export default Navbar;
