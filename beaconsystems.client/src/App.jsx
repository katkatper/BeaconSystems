import React, { lazy, Suspense, useEffect } from "react";

import { BrowserRouter as Router,Routes,Route,Navigate,useLocation,useNavigate} from "react-router-dom";

import Navbar from "./pages/Navbar.jsx";
import Login from "./pages/Login.jsx";
import "./App.css";
import BeaconInsight from "./components/BeaconInsight.jsx";

const InvestigatorWorkspace = lazy(() => import("./pages/InvestigatorWorkspace.jsx"));
const Dashboard = lazy(() => import("./pages/Dashboard.jsx"));
const MissingPersonsList = lazy(() => import("./pages/MissingPersons.jsx"));
const AddPerson = lazy(() => import("./pages/AddReport.jsx"));
const CaseDetail = lazy(() => import("./pages/CaseDetail.jsx"));
const PersonDetail = lazy(() => import("./pages/PersonDetail.jsx"));
const CreateCase = lazy(() => import("./pages/CreateCase.jsx"));
const AddExternalRecord = lazy(() => import("./pages/AddExternalRecord.jsx"));
const ExternalRecordList = lazy(() => import("./pages/ExternalRecordList.jsx"));
const Alerts = lazy(() => import("./pages/Alerts.jsx"));
const AgencyManagement = lazy(() => import("./pages/AgencyManagement.jsx"));
const UserManagement = lazy(() => import("./pages/UserManagement.jsx"));
const Cases = lazy(() => import("./pages/Cases.jsx"));
const IntelligenceCenter = lazy(() => import("./pages/IntelligenceCenter.jsx"));
const EvidenceUpload = lazy(() => import("./pages/EvidenceUpload.jsx"));
const LegalAccessRequests = lazy(() => import("./pages/LegalAccessRequests.jsx"));
const LegalOrders = lazy(() => import("./pages/LegalOrders.jsx"));
const LegalOrderDetail = lazy(() => import("./pages/LegalOrderDetail.jsx"));
const PartnerSources = lazy(() => import("./pages/PartnerSources.jsx"));
const CaseAccess = lazy(() => import("./pages/CaseAccess.jsx"));
const Sightings = lazy(() => import("./pages/Sightings.jsx"));
const Analytics = lazy(() => import("./pages/Analytics.jsx"));
const Administration = lazy(() => import("./pages/Administration.jsx"));
const CommandTools = lazy(() => import("./pages/CommandTools.jsx"));
const EscapeRouteAnalysis = lazy(() => import("./pages/EscapeRouteAnalysis.jsx"));
const BoloBoard = lazy(() => import("./pages/BoloBoard.jsx"));
const SupervisorQueue = lazy(() => import("./pages/SupervisorQueue.jsx"));
const JobOperations = lazy(() => import("./pages/JobOperations.jsx"));
const AuditCenter = lazy(() => import("./pages/AuditCenter.jsx"));

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

function RoleRoute({ allowedRoles, children }) {
    const role = localStorage.getItem("role") || "viewer";

    if (!allowedRoles.includes(role)) {
        return (
            <section className="access-denied-state" role="alert" aria-labelledby="access-denied-heading">
                <span>Restricted workspace</span>
                <h1 id="access-denied-heading">Access unavailable</h1>
                <p>Your current Beacon role does not permit this workspace. No restricted data was loaded.</p>
                <a href="/">Return to your dashboard</a>
            </section>
        );
    }

    return children;
}

const operationalRoles = ["platform_admin", "agency_admin", "supervisor"];
const investigativeRoles = [...operationalRoles, "investigator", "analyst"];
const caseMutationRoles = [...operationalRoles, "investigator"];
const administratorRoles = ["platform_admin", "agency_admin"];
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

    useEffect(() => {
        const main = document.getElementById("main-content");
        if (main) {
            main.focus({ preventScroll: true });
        }
    }, [location.pathname]);

    return (
        <>
            {!hideNavbar && <a className="skip-link" href="#main-content">Skip to main content</a>}
            {!hideNavbar && <Navbar />}

            <main
                id="main-content"
                tabIndex="-1"
                className={hideNavbar ? "app-content" : "app-content with-sidebar"}
            >
                <Suspense fallback={(
                    <div className="route-loading-state" role="status" aria-live="polite">
                        <span aria-hidden="true" />
                        Loading workspace…
                    </div>
                )}>
                <Routes>
                <Route path="/operations" element={<ProtectedRoute><RoleRoute allowedRoles={operationalRoles}><JobOperations /></RoleRoute></ProtectedRoute>} />

                <Route path="/login" element={<Login />} />

                <Route
                    path="/"
                    element={
                        <ProtectedRoute>
                            {localStorage.getItem("role") === "investigator" ? <InvestigatorWorkspace /> : <Dashboard />}
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
                            <RoleRoute allowedRoles={caseMutationRoles}><AddPerson /></RoleRoute>
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
                            <RoleRoute allowedRoles={caseMutationRoles}><CreateCase /></RoleRoute>
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/external-records/add"
                    element={
                        <ProtectedRoute>
                            <RoleRoute allowedRoles={caseMutationRoles}><AddExternalRecord /></RoleRoute>
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
                            <RoleRoute allowedRoles={investigativeRoles}><Alerts /></RoleRoute>
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/agencies"
                    element={
                        <ProtectedRoute>
                            <RoleRoute allowedRoles={operationalRoles}><AgencyManagement /></RoleRoute>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/admin/users"
                    element={
                        <ProtectedRoute>
                            <RoleRoute allowedRoles={administratorRoles}><UserManagement /></RoleRoute>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/users"
                    element={
                        <ProtectedRoute>
                            <RoleRoute allowedRoles={administratorRoles}><UserManagement /></RoleRoute>
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
                            <RoleRoute allowedRoles={investigativeRoles}><IntelligenceCenter /></RoleRoute>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/escape-routes"
                    element={
                        <ProtectedRoute>
                            <RoleRoute allowedRoles={investigativeRoles}><EscapeRouteAnalysis /></RoleRoute>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/sightings"
                    element={
                        <ProtectedRoute>
                            <RoleRoute allowedRoles={investigativeRoles}><Sightings /></RoleRoute>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/analytics"
                    element={
                        <ProtectedRoute>
                            <RoleRoute allowedRoles={[...operationalRoles, "analyst"]}><Analytics /></RoleRoute>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/administration"
                    element={
                        <ProtectedRoute>
                            <RoleRoute allowedRoles={administratorRoles}><Administration /></RoleRoute>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/command/:tool"
                    element={
                        <ProtectedRoute>
                            <RoleRoute allowedRoles={operationalRoles}><CommandTools /></RoleRoute>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/evidence-upload"
                    element={
                        <ProtectedRoute>
                            <RoleRoute allowedRoles={caseMutationRoles}><EvidenceUpload /></RoleRoute>
                        </ProtectedRoute>
                    }   
                    />
                <Route
                    path="/legal-access"
                    element={
                        <ProtectedRoute>
                            <RoleRoute allowedRoles={caseMutationRoles}><LegalAccessRequests /></RoleRoute>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/legal-orders"
                    element={
                        <ProtectedRoute>
                            <RoleRoute allowedRoles={caseMutationRoles}><LegalOrders /></RoleRoute>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/partner-sources"
                    element={
                        <ProtectedRoute>
                            <RoleRoute allowedRoles={operationalRoles}><PartnerSources /></RoleRoute>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/case-access"
                    element={
                        <ProtectedRoute>
                            <RoleRoute allowedRoles={caseMutationRoles}><CaseAccess /></RoleRoute>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/bolos"
                    element={
                        <ProtectedRoute>
                            <RoleRoute allowedRoles={operationalRoles}><BoloBoard /></RoleRoute>
                        </ProtectedRoute>
                    }
                />
                {/* Supervisor and audit pages are protected views for compliance oversight. */}
                <Route
                    path="/supervisor"
                    element={
                        <ProtectedRoute>
                            <RoleRoute allowedRoles={operationalRoles}><SupervisorQueue /></RoleRoute>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/legal-orders/:id"
                    element={
                        <ProtectedRoute>
                            <RoleRoute allowedRoles={caseMutationRoles}><LegalOrderDetail /></RoleRoute>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/supervisor/:workspace"
                    element={
                        <ProtectedRoute>
                            <RoleRoute allowedRoles={operationalRoles}><SupervisorQueue /></RoleRoute>
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/audit"
                    element={
                        <ProtectedRoute>
                            <RoleRoute allowedRoles={operationalRoles}><AuditCenter /></RoleRoute>
                        </ProtectedRoute>
                    }
                />
                </Routes>
                </Suspense>
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
