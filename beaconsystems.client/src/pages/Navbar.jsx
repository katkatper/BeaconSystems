import React from "react";
import { NavLink, useNavigate } from "react-router-dom";


// Navbar provides primary navigation after login. Role-specific links are kept
// here so users only see areas relevant to their responsibilities.
function Navbar() {
    const navigate = useNavigate();
    const role = localStorage.getItem("role");
    const username = localStorage.getItem("username") || "Beacon User";
    const navLinks = {
        admin: [
            ["Agencies", "/agencies"],
            ["Alerts", "/alerts"],
            ["Audit", "/audit"],
            ["Cases", "/cases"],
            ["Dashboard", "/"],
            ["Intelligence", "/intelligence"],
            ["Partners", "/partner-sources"],
        ],
        agency_admin: [
            ["Agencies", "/agencies"],
            ["Alerts", "/alerts"],
            ["Audit", "/audit"],
            ["Cases", "/cases"],
            ["Dashboard", "/"],
            ["Intelligence", "/intelligence"],
            ["Partners", "/partner-sources"],
        ],
        supervisor: [
            ["Agencies", "/agencies"],
            ["Alerts", "/alerts"],
            ["Audit", "/audit"],
            ["Cases", "/cases"],
            ["Dashboard", "/"],
            ["Intelligence", "/intelligence"],
            ["Partners", "/partner-sources"],
        ],
        investigator: [
            ["Alerts", "/alerts"],
            ["Cases", "/cases"],
            ["Dashboard", "/"],
            ["Intelligence", "/intelligence"],
            ["Partners", "/partner-sources"],
        ],
        analyst: [
            ["Alerts", "/alerts"],
            ["Cases", "/cases"],
            ["Dashboard", "/"],
            ["Intelligence", "/intelligence"],
            ["Partners", "/partner-sources"],
        ],
        viewer: [
            ["Cases", "/cases"],
            ["Dashboard", "/"],
        ],
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

    // Clear local session data and return the user to the login page.

    const handleLogout = () => {
        localStorage.clear();
        navigate("/login");
    };

    return (
        <nav className="navbar">
            <div className="navbar-topline">
                <div className="navbar-brand">
                    <div className="brand-mark" aria-hidden="true">
                        <span className="brand-ray brand-ray-main"></span>
                        <span className="brand-ray brand-ray-soft"></span>
                        <span className="brand-ray brand-ray-side"></span>
                    </div>
                    <div>
                        <h2>Beacon</h2>
                        <span>Recovery Intelligence Platform</span>
                    </div>
                </div>

                <div className="navbar-welcome">
                    <span>Welcome back</span>
                    <strong>
                        {displayRole} {username}
                    </strong>
                </div>
            </div>

            <div className="navbar-links">
                {visibleLinks.map(([label, path]) => (
                    <NavLink key={path} to={path}>
                        {label}
                    </NavLink>
                ))}

                <button onClick={handleLogout} className="logout-button">
                    Logout
                </button>
            </div>
        </nav>
    );
}

export default Navbar;
