import React from "react";
import { Link } from "react-router-dom";

function Navbar() {
    return (
        <nav>
            <Link to="/">Dashboard</Link>{" | "}

            <Link to="/missing">Missing Persons</Link>{" | "}

            <Link to="/add">Report Person</Link>{" | "}

            <Link to="/login">Login</Link>{" | "}

            <Link to="/create-case">Create Case</Link>{" | "}

            <Link to="/external-records/add"> Add External Record</Link> {" | "}

            <Link to="/external-records"> View External Record</Link>

        </nav>
    );
}

export default Navbar;