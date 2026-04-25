import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import Dashboard from "./pages/Dashboard.jsx";
import MissingPersonsList from "./pages/MissingPersons.jsx";
import Navbar from "./pages/Navbar.jsx";
import AddPerson from "./pages/AddReport.jsx";
import Login from "./pages/Login.jsx";

function App() {
    const [token, setToken] = useState(localStorage.getItem("token"));

    return (
        <Router>
            <Navbar />

            <Routes>
                <Route path="/login" element={<Login onLogin={setToken} />} />
                <Route path="/" element={<Dashboard />} />
                <Route path="/missing" element={<MissingPersonsList />} />
                <Route path="/add" element={<AddPerson />} />
            </Routes>
        </Router>
    );
}

export default App;