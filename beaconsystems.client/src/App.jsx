import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import Dashboard from "./pages/Dashboard.jsx";
import MissingPersonsList from "./pages/MissingPersons.jsx";
import Navbar from "./pages/Navbar.jsx";
import AddPerson from "./pages/AddReport.jsx";
import Login from "./pages/Login.jsx";
import CaseDetail from "./pages/CaseDetail.jsx";
import PersonDetail from "./pages/PersonDetail.jsx";
import CreateCase from "./pages/CreateCase.jsx";


function App() {
    return (
        <Router>
            <Navbar />

            <Routes>
                <Route path="/" element={<Dashboard />} />

                <Route path="/missing" element={<MissingPersonsList />} />

                <Route path="/add" element={<AddPerson />} />

                <Route path="/login" element={<Login />} />

                <Route path="/cases/:id" element={<CaseDetail />} />

                <Route path="/persons/:id" element={<PersonDetail />} />

                <Route path="/create-case" element={<CreateCase />} />

            </Routes>
        </Router>
    );
}

export default App;