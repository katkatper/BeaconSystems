import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import MissingPersonsList from "./MissingPersons";
import Navbar from "./components/Navbar";
import AddReport from "./pages/AddPerson";

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