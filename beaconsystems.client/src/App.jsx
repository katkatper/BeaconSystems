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
import AddExternalRecord from "./pages/AddExternalRecord.jsx";
import ExternalRecordList from "./pages/ExternalRecordList.jsx";
import Alerts from "./pages/Alerts.jsx";

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

                <Route path="/external-records/add" element={<AddExternalRecord />} />

                <Route path="/external-records" element={<ExternalRecordList />} />

                <Route path="/alerts" element={<Alerts />} />
            </Routes>
        </Router>
    );
}

export default App;