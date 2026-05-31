import React from "react";
import { NavLink, useNavigate } from "react-router-dom";


// Navbar provides primary navigation after login. Role-specific links are kept
// here so users only see areas relevant to their responsibilities.
function Navbar() {
    const navigate = useNavigate();
    const role = localStorage.getItem("role");
    const username = localStorage.getItem("username") || "Beacon User";
    const roleLabels = {
        admin: "Administrator",
        agency_admin: "Supervisor",
        investigator: "Detective",
        analyst: "Analyst",
        viewer: "Viewer",
    };
    const displayRole = roleLabels[role] || "Team Member";

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
                <NavLink to="/">Dashboard</NavLink>
                <NavLink to="/cases">Cases</NavLink>
                <NavLink to="/supervisor">Supervisor</NavLink>

                {role === "admin" && (
                    <NavLink to="/agencies">Agencies</NavLink>
                )}

                <button onClick={handleLogout} className="logout-button">
                    Logout
                </button>
            </div>
        </nav>
    );
}

export default Navbar;
