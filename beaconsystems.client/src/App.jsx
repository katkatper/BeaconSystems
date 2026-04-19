import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard.jsx";
import MissingPersonsList from "./MissingPersons.jsx";
import Navbar from "./components/Navbar.jsx";
import AddPerson from "./pages/AddPerson.jsx";

function App() {
    return (
        <Router>

          <Navbar  />
            <h1> Beacon Systems Dashboard</h1>

            <Routes>

                <Route path="/" element={<Dashboard />} />

                <Route path="/missing" element={<MissingPersonsList />} />

                <Route path="/add" element={<AddPerson />} />

        </Routes>
        
        </Router >
         
     );

}
export default App;
