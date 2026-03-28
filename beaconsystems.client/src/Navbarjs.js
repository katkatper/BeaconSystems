import React from "react";
import { Link } from "react-router-dom";

function Navbar() {
    return (
        <nav>
            <Link to="/"></Link> |{" "}
            <Link to="/missing">Missing Persons</Link>
            <Link to= "/add"> Report Person </Link>
        </nav>


    );


}
export default Navbar;