import React from "react";
import { NavLink, useNavigate } from "react-router-dom";


// Navbar provides primary navigation after login. Role-specific links are kept
// here so users only see areas relevant to their responsibilities.
function Navbar() {
    const navigate = useNavigate();
    const role = localStorage.getItem("role");

    // Clear local session data and return the user to the login page.

    const handleLogout = () => {
        localStorage.clear();
        navigate("/login");
    };

    return (
        <nav className="navbar">
            <div className="navbar-brand">
                <div className="brand-mark">B</div>
                <div>
                    <h2>Beacon</h2>
                    <span>Investigative Intelligence</span>
                </div>
            </div>

            <div className="navbar-links">
                <NavLink to="/">Dashboard</NavLink>
                <NavLink to="/cases">Cases</NavLink>
                <NavLink to="/case-access">Case Access</NavLink>
                <NavLink to="/evidence-upload">Evidence</NavLink>
                <NavLink to="/intelligence">Intelligence</NavLink>
                <NavLink to="/bolos">BOLO</NavLink>
                <NavLink to="/legal-access">Legal Access</NavLink>
                <NavLink to="/partner-sources">Partners</NavLink>
                <NavLink to="/supervisor">Supervisor</NavLink>
                <NavLink to="/audit">Audit</NavLink>


                {/* Admin-only management links. Backend role checks still enforce access. */}

                {(role === "admin" || role === "agency_admin" || role === "investigator") && (
                    <NavLink to="/alerts">Alerts</NavLink>
                )}

                {role === "admin" && (
                    <>
                        <NavLink to="/agencies">Agencies</NavLink>
                        <NavLink to="/admin/users">Users</NavLink>
                    </>
                )}

                <button onClick={handleLogout} className="logout-button">
                    Logout
                </button>
            </div>
        </nav>
    );
}

export default Navbar;
