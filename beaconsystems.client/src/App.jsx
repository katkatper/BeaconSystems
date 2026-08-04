import React, { useEffect } from "react";

import { BrowserRouter as Router,Routes,Route,Navigate,useLocation,useNavigate} from "react-router-dom";

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
import EscapeRouteAnalysis from "./pages/EscapeRouteAnalysis.jsx";
import "./App.css";
import BoloBoard from "./pages/BoloBoard.jsx";
import SupervisorQueue from "./pages/SupervisorQueue";
import AuditCenter from "./pages/AuditCenter.jsx";
import BeaconInsight from "./components/BeaconInsight.jsx";

const SESSION_IDLE_TIMEOUT_MS = 30 * 60 * 1000;

function clearAuthSession(message) {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("username");
    localStorage.removeItem("agency_id");
    localStorage.removeItem("last_activity_at");
    localStorage.removeItem("session_expires_at");

    if (message) {
        localStorage.setItem("session_timeout_message", message);
    }
}

function isSessionExpired() {
    const lastActivityAt = Number(localStorage.getItem("last_activity_at") || Date.now());
    const sessionExpiresAt = localStorage.getItem("session_expires_at");
    const absoluteExpiresAt = sessionExpiresAt ? Date.parse(sessionExpiresAt) : null;
    const now = Date.now();

    return (
        now - lastActivityAt > SESSION_IDLE_TIMEOUT_MS ||
        (absoluteExpiresAt && now > absoluteExpiresAt)
    );
}

// ProtectedRoute keeps application pages behind login. The backend still
// enforces real authorization; this only controls frontend navigation.

function ProtectedRoute({ children }) {
    const token = localStorage.getItem("token");

    if (!token || isSessionExpired()) {
        if (token) {
            clearAuthSession("Your Beacon session expired. Please sign in again.");
        }

        return <Navigate to="/login" replace />;
    }

    return children;
}
// AppLayout owns the shared navigation and page routes. Login hides the navbar
// so unauthenticated users only see the sign-in screen.
function AppLayout() {
    const location = useLocation();
    const navigate = useNavigate();

    const hideNavbar = location.pathname === "/login";

    useEffect(() => {
        if (hideNavbar || !localStorage.getItem("token")) {
            return undefined;
        }

        const recordActivity = () => {
            localStorage.setItem("last_activity_at", String(Date.now()));
        };

        const checkSession = () => {
            if (localStorage.getItem("token") && isSessionExpired()) {
                clearAuthSession("Your Beacon session expired. Please sign in again.");
                navigate("/login", { replace: true });
            }
        };

        const activityEvents = ["click", "keydown", "mousemove", "scroll", "touchstart"];
        activityEvents.forEach((eventName) =>
            window.addEventListener(eventName, recordActivity, { passive: true })
        );

        const interval = window.setInterval(checkSession, 15000);
        recordActivity();

        return () => {
            activityEvents.forEach((eventName) =>
                window.removeEventListener(eventName, recordActivity)
            );
            window.clearInterval(interval);
        };
    }, [hideNavbar, navigate]);

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
                    path="/escape-routes"
                    element={
                        <ProtectedRoute>
                            <EscapeRouteAnalysis />
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
            {!hideNavbar && localStorage.getItem("token") && <BeaconInsight />}
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
