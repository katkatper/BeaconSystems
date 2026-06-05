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
            ["Dashboard", "/"],
            ["Cases", "/cases"],
            ["Case Access", "/case-access"],
            ["Evidence", "/evidence-upload"],
            ["Intelligence", "/intelligence"],
            ["BOLO", "/bolos"],
            ["Request Legal Access", "/legal-access"],
            ["Legal Orders", "/legal-orders"],
            ["Partners", "/partner-sources"],
            ["Supervisor", "/supervisor"],
            ["Audit", "/audit"],
            ["Alerts", "/alerts"],
            ["Agencies", "/agencies"],
            ["Users", "/admin/users"],
        ],
        agency_admin: [
            ["Dashboard", "/"],
            ["Cases", "/cases"],
            ["Case Access", "/case-access"],
            ["Evidence", "/evidence-upload"],
            ["Intelligence", "/intelligence"],
            ["BOLO", "/bolos"],
            ["Request Legal Access", "/legal-access"],
            ["Legal Orders", "/legal-orders"],
            ["Partners", "/partner-sources"],
            ["Supervisor", "/supervisor"],
            ["Alerts", "/alerts"],
            ["Agencies", "/agencies"],
        ],
        supervisor: [
            ["Dashboard", "/"],
            ["Cases", "/cases"],
            ["Case Access", "/case-access"],
            ["Evidence", "/evidence-upload"],
            ["Intelligence", "/intelligence"],
            ["BOLO", "/bolos"],
            ["Request Legal Access", "/legal-access"],
            ["Legal Orders", "/legal-orders"],
            ["Partners", "/partner-sources"],
            ["Supervisor", "/supervisor"],
            ["Alerts", "/alerts"],
        ],
        investigator: [
            ["Dashboard", "/"],
            ["My Cases", "/cases"],
            ["Case Access", "/case-access"],
            ["Evidence", "/evidence-upload"],
            ["Intelligence", "/intelligence"],
            ["BOLO", "/bolos"],
            ["Request Legal Access", "/legal-access"],
            ["Partner Data", "/partner-sources"],
        ],
        analyst: [
            ["Dashboard", "/"],
            ["Cases", "/cases"],
            ["Evidence", "/evidence-upload"],
            ["Intelligence", "/intelligence"],
            ["BOLO", "/bolos"],
            ["Partner Data", "/partner-sources"],
        ],
        viewer: [
            ["Dashboard", "/"],
            ["Cases", "/cases"],
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
