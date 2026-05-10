import React from "react";
import { Link } from "react-router-dom";

function Navbar() {

    return (

        <nav style={styles.nav}>

            <h2 style={styles.title}>Beacon Systems</h2>

            <div>

                <Link to="/" style={styles.link}>
                    Dashboard
                </Link>

                <Link to="/missing" style={styles.link}>
                    Missing Persons
                </Link>

                <Link to="/cases/1" style={styles.link}>
                    Cases
                </Link>

                <Link to="/external-records" style={styles.link}>
                    External Records
                </Link>

                <Link to="/alerts" style={styles.link}>
                    Alerts
                </Link>

                <Link to="/login" style={styles.link}>
                    Login
                </Link>

            </div>

        </nav>
    );
}

const styles = {

    nav: {
        backgroundColor: "#1e293b",
        padding: "15px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
    },

    title: {
        color: "white",
        margin: 0,
    },

    link: {
        color: "white",
        marginRight: "15px",
        textDecoration: "none",
        fontWeight: "bold",
    },
};

export default Navbar;