import React from "react";
import { Link, useNavigate } from "react-router-dom";


function Navbar() {

    const navigate = useNavigate();

    const role = localStorage.getItem("role");

    const handleLogout = () => {

        localStorage.removeItem("token");

        localStorage.removeItem("role");

        localStorage.removeItem("user_id");

        localStorage.removeItem("agency_id");

        navigate("/login");
    };


    return (
        <nav style={styles.nav}>

            <h2>Beacon System</h2>

            <div>
                <Link to="/" style={styles.link}>Dashboard</Link>

                <Link to="/cases" style={styles.link}>Cases</Link>

                <Link to="/missing" style={styles.link}>Missing Persons</Link>

                <Link to="/create-case" style={styles.link}>Create Case</Link>

                <Link to="/external-records" style={styles.link}>External Records</Link>

                {(role === "admin" || role === "agency_admin" || role === "investigator") && (

                    <Link to="/alerts" style={styles.link}>Alerts</Link>

                )}

                <Link to="/intelligence" style={styles.link}>
                    Intelligence Center
                </Link>

                {role === "admin" && (
                    <>
                        <Link to="/agencies" style={styles.link}>Agencies</Link>

                        <Link to="/admin/users" style={styles.link}>Users</Link>
                    </>
                )}

                <button onClick={handleLogout} style={styles.button}>
                    Logout
                </button>

            </div>
        </nav>
    );
}

const styles = {

    nav: {
        padding: "15px",
        backgroundColor: "#111",
        color: "white",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
    },

    link: {
        color: "white",
        marginRight: "15px",
        textDecoration: "none",
    },

    button: {
        padding: "6px 12px",
        cursor: "pointer",
    },
};

export default Navbar;