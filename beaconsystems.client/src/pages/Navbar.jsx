import React from "react";
import { Link } from "react-router-dom";

function Navbar() {
    return (
        <nav>
            <Link to="/">Dashboard</Link>{" | "}
            <Link to="/missing">Missing Persons</Link>{" | "}
            <Link to="/add">Report Person</Link>{" | "}
            <Link to="/login">Login</Link>
        </nav>
    );
}

export default Navbar;