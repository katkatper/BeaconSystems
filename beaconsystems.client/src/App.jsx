import React from "react";

import { BrowserRouter as Router,Routes,Route,Navigate,useLocation} from "react-router-dom";

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
import AgencyManagement from "./pages/AgencyManagement.jsx";
import UserManagement from "./pages/UserManagement.jsx";
import Cases from "./pages/Cases.jsx";
import IntelligenceCenter from "./pages/IntelligenceCenter.jsx";
import EvidenceUpload from "./pages/EvidenceUpload.jsx";
import LegalAccessRequests from "./pages/LegalAccessRequests.jsx";
import LegalOrders from "./pages/LegalOrders.jsx";
import LegalOrderDetail from "./pages/LegalOrderDetail.jsx";
import PartnerSources from "./pages/PartnerSources.jsx";
import CaseAccess from "./pages/CaseAccess.jsx";
import Sightings from "./pages/Sightings.jsx";
import Analytics from "./pages/Analytics.jsx";
import Administration from "./pages/Administration.jsx";
import CommandTools from "./pages/CommandTools.jsx";
import "./App.css";
import BoloBoard from "./pages/BoloBoard.jsx";
import SupervisorQueue from "./pages/SupervisorQueue";
import AuditCenter from "./pages/AuditCenter.jsx";


// ProtectedRoute keeps application pages behind login. The backend still
// enforces real authorization; this only controls frontend navigation.

function ProtectedRoute({ children }) {
    const token = localStorage.getItem("token");

    if (!token) {
        return <Navigate to="/login" replace />;
    }

    return children;
}
// AppLayout owns the shared navigation and page routes. Login hides the navbar
// so unauthenticated users only see the sign-in screen.
function AppLayout() {
    const location = useLocation();

    const hideNavbar = location.pathname === "/login";

    return (
        <>
            {!hideNavbar && <Navbar />}

            <main className={hideNavbar ? "app-content" : "app-content with-sidebar"}>
                <Routes>

                <Route path="/login" element={<Login />} />

                <Route
                    path="/"
                    element={
                        <ProtectedRoute>
                            <Dashboard />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/missing"
                    element={
                        <ProtectedRoute>
                            <MissingPersonsList />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/add"
                    element={
                        <ProtectedRoute>
                            <AddPerson />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/cases/:id"
                    element={
                        <ProtectedRoute>
                            <CaseDetail />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/persons/:id"
                    element={
                        <ProtectedRoute>
                            <PersonDetail />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/create-case"
                    element={
                        <ProtectedRoute>
                            <CreateCase />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/external-records/add"
                    element={
                        <ProtectedRoute>
                            <AddExternalRecord />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/external-records"
                    element={
                        <ProtectedRoute>
                            <ExternalRecordList />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/alerts"
                    element={
                        <ProtectedRoute>
                            <Alerts />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/agencies"
                    element={
                        <ProtectedRoute>
                            <AgencyManagement />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/admin/users"
                    element={
                        <ProtectedRoute>
                            <UserManagement />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/users"
                    element={
                        <ProtectedRoute>
                            <UserManagement />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/cases"
                    element={
                        <ProtectedRoute>
                            <Cases />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/intelligence"
                    element={
                        <ProtectedRoute>
                            <IntelligenceCenter />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/sightings"
                    element={
                        <ProtectedRoute>
                            <Sightings />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/analytics"
                    element={
                        <ProtectedRoute>
                            <Analytics />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/administration"
                    element={
                        <ProtectedRoute>
                            <Administration />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/command/:tool"
                    element={
                        <ProtectedRoute>
                            <CommandTools />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/evidence-upload"
                    element={
                        <ProtectedRoute>
                            <EvidenceUpload />
                        </ProtectedRoute>
                    }   
                    />
                <Route
                    path="/legal-access"
                    element={
                        <ProtectedRoute>
                            <LegalAccessRequests />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/legal-orders"
                    element={
                        <ProtectedRoute>
                            <LegalOrders />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/partner-sources"
                    element={
                        <ProtectedRoute>
                            <PartnerSources />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/case-access"
                    element={
                        <ProtectedRoute>
                            <CaseAccess />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/bolos"
                    element={
                        <ProtectedRoute>
                            <BoloBoard />
                        </ProtectedRoute>
                    }
                />
                {/* Supervisor and audit pages are protected views for compliance oversight. */}
                <Route
                    path="/supervisor"
                    element={
                        <ProtectedRoute>
                            <SupervisorQueue />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/legal-orders/:id"
                    element={
                        <ProtectedRoute>
                            <LegalOrderDetail />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/supervisor/:workspace"
                    element={
                        <ProtectedRoute>
                            <SupervisorQueue />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/audit"
                    element={
                        <ProtectedRoute>
                            <AuditCenter />
                        </ProtectedRoute>
                    }
                />
                </Routes>
            </main>
        </>
    );
}
// App wraps the router in the shared Beacon background shell.
function App() {
    return (
        <div className="main-background">
            <Router>
                <AppLayout />
            </Router>
        </div>
    );
}

export default App;
