import React, { useState, useEffect } from "react";
import { apiGet, apiPatch, apiPost, apiUrl } from "../api.jsx";


const starterAgencies = [
    {
        agency_id: "starter-ncmec",
        agency_name: "National Center for Missing & Exploited Children (NCMEC)",
        agency_type: "Missing children clearinghouse",
        city: "Alexandria",
        state: "VA",
        country: "USA",
        contact_phone: "1-800-THE-LOST (1-800-843-5678)",
        address: "333 John Carlyle Street, Suite 125, Alexandria, VA 22314",
        website: "https://www.missingkids.org",
    },
    {
        agency_id: "starter-houston-icac",
        agency_name: "Houston Metro Internet Crimes Against Children (ICAC)",
        agency_type: "Internet crimes against children task force",
        city: "Houston",
        state: "TX",
        country: "USA",
        contact_phone: "713-884-3131",
        address: "Houston Police Department, 1200 Travis Street, Houston, TX 77002",
        website: "https://www.icactaskforce.org",
    },
    {
        agency_id: "starter-houston-police",
        agency_name: "Houston Police Department",
        agency_type: "Municipal law enforcement",
        city: "Houston",
        state: "TX",
        country: "USA",
        contact_phone: "(713) 884-3131",
        address: "1200 Travis Street, Houston, TX 77002",
        website: "https://www.houstontx.gov/police",
    },
    {
        agency_id: "starter-fbi",
        agency_name: "Federal Bureau of Investigation (FBI)",
        agency_type: "Federal law enforcement",
        city: "Washington",
        state: "DC",
        country: "USA",
        contact_phone: "202-324-3000",
        address: "935 Pennsylvania Avenue NW, Washington, DC 20535",
        website: "https://www.fbi.gov/contact-us",
    },
    {
        agency_id: "starter-chi",
        agency_name: "Center for Human Identification",
        agency_type: "Forensic identification and missing persons support",
        city: "Fort Worth",
        state: "TX",
        country: "USA",
        contact_phone: "817-735-0606",
        address: "3500 Camp Bowie Boulevard, Fort Worth, TX 76107",
        website: "https://www.unthsc.edu/center-for-human-identification",
    },
    {
        agency_id: "starter-ovc",
        agency_name: "Office for Victims of Crime (OVC)",
        agency_type: "Victim services and federal support",
        city: "Washington",
        state: "DC",
        country: "USA",
        contact_phone: "1-800-851-3420",
        address: "810 Seventh Street NW, Washington, DC 20531",
        website: "https://ovc.ojp.gov",
    },
    {
        agency_id: "starter-namus",
        agency_name: "National Missing and Unidentified Persons System (NamUs)",
        agency_type: "Missing and unidentified persons system",
        city: "Washington",
        state: "DC",
        country: "USA",
        contact_phone: "1-855-626-7600",
        address: "810 Seventh Street NW, Washington, DC 20531",
        website: "https://namus.nij.ojp.gov",
    },
    {
        agency_id: "starter-texas-dps",
        agency_name: "Texas Department of Public Safety",
        agency_type: "State law enforcement",
        city: "Austin",
        state: "TX",
        country: "USA",
        contact_phone: "512-424-2000",
        address: "5805 North Lamar Boulevard, Austin, TX 78752",
        website: "https://www.dps.texas.gov",
    },
    {
        agency_id: "starter-texas-dps-houston-regional",
        agency_name: "Texas Department of Public Safety - Houston Regional Office",
        agency_type: "State law enforcement and highway patrol",
        city: "Houston",
        state: "TX",
        country: "USA",
        contact_phone: "(281) 517-1200",
        address: "12230 West Road, Houston, TX 77065",
        website: "https://www.dps.texas.gov",
    },
    {
        agency_id: "starter-texas-rangers-houston-company",
        agency_name: "Texas Rangers - Houston Company Headquarters",
        agency_type: "State criminal investigations",
        city: "Houston",
        state: "TX",
        country: "USA",
        contact_phone: "(281) 517-1200",
        address: "12230 West Road, Houston, TX 77065",
        website: "https://www.dps.texas.gov/section/texas-rangers",
    },
    {
        agency_id: "starter-austin-police",
        agency_name: "Austin Police Department",
        agency_type: "Municipal law enforcement",
        city: "Austin",
        state: "TX",
        country: "USA",
        contact_phone: "(512) 974-5000; non-emergency 311 or (512) 974-2000",
        address: "715 E. 8th Street, Austin, TX 78701",
        website: "https://www.austintexas.gov/department/police",
    },
    {
        agency_id: "starter-texas-dps-headquarters",
        agency_name: "Texas Department of Public Safety Headquarters",
        agency_type: "State law enforcement headquarters",
        city: "Austin",
        state: "TX",
        country: "USA",
        contact_phone: "(512) 424-2000",
        address: "5805 North Lamar Boulevard, Austin, TX 78752",
        website: "https://www.dps.texas.gov",
    },
    {
        agency_id: "starter-texas-rangers-headquarters",
        agency_name: "Texas Rangers Headquarters",
        agency_type: "State criminal investigations headquarters",
        city: "Austin",
        state: "TX",
        country: "USA",
        contact_phone: "(512) 424-2000",
        address: "5805 North Lamar Boulevard, Austin, TX 78752",
        website: "https://www.dps.texas.gov/section/texas-rangers",
    },
    {
        agency_id: "starter-dallas-police",
        agency_name: "Dallas Police Department",
        agency_type: "Municipal law enforcement",
        city: "Dallas",
        state: "TX",
        country: "USA",
        contact_phone: "(214) 671-3001",
        address: "1400 Botham Jean Boulevard, Dallas, TX 75215",
        website: "https://dallaspolice.net",
    },
    {
        agency_id: "starter-texas-dps-dallas",
        agency_name: "Texas Department of Public Safety - Dallas Office",
        agency_type: "State law enforcement and highway patrol",
        city: "Dallas",
        state: "TX",
        country: "USA",
        contact_phone: "(214) 861-3700",
        address: "5700 East Northwest Highway, Dallas, TX 75231",
        website: "https://www.dps.texas.gov",
    },
    {
        agency_id: "starter-texas-rangers-company-b",
        agency_name: "Texas Rangers Company B",
        agency_type: "State criminal investigations",
        city: "Dallas",
        state: "TX",
        country: "USA",
        contact_phone: "(214) 861-3700",
        address: "5700 East Northwest Highway, Dallas, TX 75231",
        website: "https://www.dps.texas.gov/section/texas-rangers",
    },
    {
        agency_id: "starter-texas-alerts",
        agency_name: "AMBER, Blue, Silver & Endangered Missing Persons Alert Programs",
        agency_type: "Public safety alert programs",
        city: "Austin",
        state: "TX",
        country: "USA",
        contact_phone: "512-424-2208",
        address: "Texas Department of Public Safety, 5805 North Lamar Boulevard, Austin, TX 78752",
        website: "https://www.dps.texas.gov/section/intelligence-counterterrorism/statewide-alert-programs",
    },
    {
        agency_id: "starter-travis-medical-examiner",
        agency_name: "Travis County Medical Examiner & Coroner",
        agency_type: "Medical examiner and coroner",
        city: "Austin",
        state: "TX",
        country: "USA",
        contact_phone: "(512) 854-9599",
        address: "7723 Springdale Road, Austin, TX 78724",
        website: "https://www.traviscountytx.gov/medical-examiner",
    },
    {
        agency_id: "starter-harris-medical-examiner",
        agency_name: "Harris County Medical Examiner & Coroner",
        agency_type: "Medical examiner and coroner",
        city: "Houston",
        state: "TX",
        country: "USA",
        contact_phone: "(713) 796-6775",
        address: "1885 Old Spanish Trail, Houston, TX 77030",
        website: "https://www.harristx.org/Medical_Examiner.html",
    },
    {
        agency_id: "starter-dallas-medical-examiner",
        agency_name: "Dallas County Medical Examiner & Coroner",
        agency_type: "Medical examiner and coroner",
        city: "Dallas",
        state: "TX",
        country: "USA",
        contact_phone: "(214) 920-5900",
        address: "2355 North Stemmons Freeway, Dallas, TX 75207",
        website: "https://www.dallascounty.org/departments/swifs/",
    },
    {
        agency_id: "starter-ice-hsi-houston",
        agency_name: "U.S. Immigration and Customs Enforcement - HSI Houston",
        agency_type: "Federal investigative field office",
        city: "Spring",
        state: "TX",
        country: "USA",
        contact_phone: "(281) 465-3900",
        address: "25700 Interstate 45 North, Suite 200, Havenwood Office Park, Spring, TX 77386",
        website: "https://www.ice.gov/hsi",
    },
];

const mergeAgencies = (apiAgencies) => {
    const normalizedNames = new Set(
        apiAgencies.map((agency) => agency.agency_name?.trim().toLowerCase()).filter(Boolean)
    );

    return [
        ...apiAgencies,
        ...starterAgencies.filter(
            (agency) => !normalizedNames.has(agency.agency_name.toLowerCase())
        ),
    ];
};

const requestTypes = [
    "Incident Report",
    "Arrest Report",
    "CAD Call Records",
    "Body Camera Footage",
    "Evidence",
    "Criminal History",
    "Intelligence Bulletin",
    "Cell Phone Records",
    "Surveillance Video",
    "DNA Analysis",
    "Fingerprint Comparison",
    "Dental Comparison",
    "Toxicology Report",
    "Lab Submission",
    "Evidence Transfer",
    "Hospital Inquiry",
    "Mental Health Facility Inquiry",
    "Morgue Comparison",
    "Decedent Identification",
    "NamUs Entry",
    "Missing Person Organization Referral",
    "Fusion Center Bulletin",
    "Family Portal Coordination",
    "Emergency Disclosure Request",
    "Search Warrant",
    "Arrest Warrant",
    "Subpoena",
    "Court Order",
    "Prosecutor Filing Packet",
    "Grand Jury Request",
    "Interagency RFI",
    "Preservation Request",
];

const legalAuthorities = [
    "Inter-agency request",
    "Supervisor approval",
    "Search warrant",
    "Court order",
    "Subpoena",
    "Mutual aid agreement",
];

const deliveryMethods = [
    "Secure Beacon portal",
    "CJIS email",
    "Encrypted email",
    "RMS portal",
    "CJIS network",
    "Physical media",
];

const statusLabels = {
    draft: "Draft",
    submitted: "Submitted",
    under_review: "Under Review",
    additional_information_requested: "Additional Information Requested",
    approved: "Approved",
    denied: "Denied",
    fulfilled: "Fulfilled",
    closed: "Closed",
};

const initialRequestForm = {
    case_id: "",
    from_agency: "Dallas Police Department",
    to_agency: "Houston Police Department",
    requesting_officer: "",
    badge_number: "",
    subject: "",
    request_type: "Incident Report",
    priority: "routine",
    due_date: "",
    assigned_to: "",
    legal_authority: "Inter-agency request",
    delivery_method: "Secure Beacon portal",
    requested_records: "",
    reason: "",
    summary: "",
};

const initialAgencyForm = {
    agency_name: "",
    agency_type: "Law Enforcement",
    city: "",
    state: "",
    country: "United States",
    contact_phone: "",
    contact_email: "",
};


function AgencyManagement() {
    const [agencies, setAgencies] = useState([]);
    const [message, setMessage] = useState("");
    const [expandedAgencyId, setExpandedAgencyId] = useState(null);
    const [agencySearch, setAgencySearch] = useState("");
    const [visibleAgencyCount, setVisibleAgencyCount] = useState(2);
    const [agencyRequests, setAgencyRequests] = useState([]);
    const [requestForm, setRequestForm] = useState(initialRequestForm);
    const [expandedRequestId, setExpandedRequestId] = useState(null);
    const [visibleRequestCount, setVisibleRequestCount] = useState(2);
    const [agencyForm, setAgencyForm] = useState(initialAgencyForm);
    const [statusDrafts, setStatusDrafts] = useState({});
    const [lifecycleBusyId, setLifecycleBusyId] = useState(null);

    const token = localStorage.getItem("token");
    const isPlatformAdmin = localStorage.getItem("role") === "platform_admin";

    const refreshAgencies = async () => {
        const data = await apiGet("/agencies/");
        setAgencies(mergeAgencies(Array.isArray(data) ? data : []));
    };

    useEffect(() => {
        let isMounted = true;

        const loadAgencies = async () => {
            try {
                const response = await fetch(apiUrl("/agencies/"), {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });

                if (!response.ok) {
                    throw new Error("Failed to load agencies");
                }

                const data = await response.json();

                if (isMounted) {
                    setAgencies(mergeAgencies(Array.isArray(data) ? data : []));
                    setMessage("");
                }
            } catch (err) {
                console.error(err);
                if (isMounted) {
                    setAgencies(starterAgencies);
                    setMessage("Showing starter agency directory. Could not load database agencies.");
                }
            }
        };

        loadAgencies();

        return () => {
            isMounted = false;
        };
    }, [token]);

    useEffect(() => {
        let isMounted = true;

        const loadAgencyRequests = async () => {
            try {
                const data = await apiGet("/agency-exchanges/");

                if (isMounted) {
                    setAgencyRequests(Array.isArray(data) ? data : []);
                }
            } catch (err) {
                console.error(err);
            }
        };

        loadAgencyRequests();

        return () => {
            isMounted = false;
        };
    }, []);

    const updateRequestForm = (field, value) => {
        setRequestForm((current) => ({
            ...current,
            [field]: value,
        }));
    };

    const updateAgencyForm = (field, value) => {
        setAgencyForm((current) => ({ ...current, [field]: value }));
    };

    const submitAgency = async (event) => {
        event.preventDefault();
        setMessage("");
        try {
            await apiPost("/agencies/", agencyForm);
            await refreshAgencies();
            setAgencyForm(initialAgencyForm);
            setMessage("Agency created and audit logged.");
        } catch (err) {
            setMessage(err.message || "Could not create agency.");
        }
    };

    const updateLifecycleDraft = (agencyId, field, value) => {
        setStatusDrafts((current) => ({
            ...current,
            [agencyId]: {
                status: current[agencyId]?.status || "active",
                reason: current[agencyId]?.reason || "",
                [field]: value,
            },
        }));
    };

    const submitLifecycleChange = async (agency) => {
        const draft = statusDrafts[agency.agency_id] || {};
        if (!draft.status || (draft.reason || "").trim().length < 10) {
            setMessage("Choose a status and enter a reason of at least 10 characters.");
            return;
        }
        setLifecycleBusyId(agency.agency_id);
        setMessage("");
        try {
            const result = await apiPatch(`/agencies/${agency.agency_id}/status`, draft);
            await refreshAgencies();
            setStatusDrafts((current) => ({ ...current, [agency.agency_id]: undefined }));
            setMessage(`Agency status updated. ${result.affected_users} user account(s) affected.`);
        } catch (err) {
            setMessage(err.message || "Could not update agency status.");
        } finally {
            setLifecycleBusyId(null);
        }
    };

    const submitAgencyRequest = async (event) => {
        event.preventDefault();
        setMessage("");

        if (!requestForm.case_id) {
            setMessage("Enter a case number before creating an inter-agency request.");
            return;
        }

        const payload = {
            ...requestForm,
            case_id: Number(requestForm.case_id),
            information_type: requestForm.request_type,
            status: "submitted",
            due_date: requestForm.due_date ? new Date(requestForm.due_date).toISOString() : null,
        };

        try {
            await apiPost("/agency-exchanges/", payload);
            const data = await apiGet("/agency-exchanges/");
            setAgencyRequests(Array.isArray(data) ? data : []);
            setRequestForm(initialRequestForm);
            setMessage("Inter-agency request submitted and audit logged.");
        } catch (err) {
            console.error(err);
            setMessage(err.message || "Could not submit inter-agency request.");
        }
    };

    const filteredAgencies = agencies
        .filter((agency) => {
            const searchText = [
                agency.agency_name,
                agency.agency_type,
                agency.city,
                agency.state,
                agency.country,
                agency.contact_phone,
                agency.address,
            ]
                .filter(Boolean)
                .join(" ")
                .toLowerCase();

            return searchText.includes(agencySearch.trim().toLowerCase());
        })
        .sort((firstAgency, secondAgency) => {
            return (firstAgency.agency_name || "").localeCompare(secondAgency.agency_name || "");
        });

    return (
        <div className="agencies-page">
            <div className="agencies-header">
                <h1>Agency Management</h1>
            </div>

            {message && <p className="alert-banner">{message}</p>}

            {isPlatformAdmin && (
                <section className="agency-governance-panel" aria-labelledby="agency-governance-heading">
                    <div className="audit-panel-heading">
                        <span>Platform Administration</span>
                        <strong id="agency-governance-heading">Controlled Agency Onboarding</strong>
                    </div>
                    <form className="agency-onboarding-form" onSubmit={submitAgency}>
                        <input required placeholder="Agency name" value={agencyForm.agency_name} onChange={(event) => updateAgencyForm("agency_name", event.target.value)} />
                        <input required placeholder="Agency type" value={agencyForm.agency_type} onChange={(event) => updateAgencyForm("agency_type", event.target.value)} />
                        <input placeholder="City" value={agencyForm.city} onChange={(event) => updateAgencyForm("city", event.target.value)} />
                        <input placeholder="State / Province" value={agencyForm.state} onChange={(event) => updateAgencyForm("state", event.target.value)} />
                        <input required placeholder="Country" value={agencyForm.country} onChange={(event) => updateAgencyForm("country", event.target.value)} />
                        <input placeholder="Contact phone" value={agencyForm.contact_phone} onChange={(event) => updateAgencyForm("contact_phone", event.target.value)} />
                        <input type="email" placeholder="Contact email" value={agencyForm.contact_email} onChange={(event) => updateAgencyForm("contact_email", event.target.value)} />
                        <button type="submit">Create Agency</button>
                    </form>
                    <small>Verify authorization and approval evidence before onboarding. All changes are audit logged.</small>
                </section>
            )}

            <section className="interagency-hub-panel">
                <div className="audit-panel-heading">
                    <span>Request Hub</span>
                    <strong>Inter-Agency Information Requests</strong>
                </div>

                <div className="interagency-hub-grid">
                    <form className="interagency-request-form" onSubmit={submitAgencyRequest}>
                        <h2>New Request</h2>

                        <div className="form-two-column">
                            <input
                                type="number"
                                placeholder="Case Number"
                                value={requestForm.case_id}
                                onChange={(event) => updateRequestForm("case_id", event.target.value)}
                            />
                            <input
                                placeholder="Subject"
                                value={requestForm.subject}
                                onChange={(event) => updateRequestForm("subject", event.target.value)}
                            />
                            <input
                                placeholder="Requesting Agency"
                                value={requestForm.from_agency}
                                onChange={(event) => updateRequestForm("from_agency", event.target.value)}
                            />
                            <input
                                placeholder="Receiving Agency"
                                value={requestForm.to_agency}
                                onChange={(event) => updateRequestForm("to_agency", event.target.value)}
                            />
                            <input
                                placeholder="Requesting Officer"
                                value={requestForm.requesting_officer}
                                onChange={(event) => updateRequestForm("requesting_officer", event.target.value)}
                            />
                            <input
                                placeholder="Badge Number"
                                value={requestForm.badge_number}
                                onChange={(event) => updateRequestForm("badge_number", event.target.value)}
                            />
                            <select
                                value={requestForm.request_type}
                                onChange={(event) => updateRequestForm("request_type", event.target.value)}
                            >
                                {requestTypes.map((type) => (
                                    <option key={type} value={type}>{type}</option>
                                ))}
                            </select>
                            <select
                                value={requestForm.priority}
                                onChange={(event) => updateRequestForm("priority", event.target.value)}
                            >
                                <option value="routine">Routine</option>
                                <option value="priority">Priority</option>
                                <option value="urgent">Urgent</option>
                            </select>
                            <select
                                value={requestForm.legal_authority}
                                onChange={(event) => updateRequestForm("legal_authority", event.target.value)}
                            >
                                {legalAuthorities.map((authority) => (
                                    <option key={authority} value={authority}>{authority}</option>
                                ))}
                            </select>
                            <select
                                value={requestForm.delivery_method}
                                onChange={(event) => updateRequestForm("delivery_method", event.target.value)}
                            >
                                {deliveryMethods.map((method) => (
                                    <option key={method} value={method}>{method}</option>
                                ))}
                            </select>
                            <input
                                type="datetime-local"
                                value={requestForm.due_date}
                                onChange={(event) => updateRequestForm("due_date", event.target.value)}
                            />
                            <input
                                placeholder="Assigned To"
                                value={requestForm.assigned_to}
                                onChange={(event) => updateRequestForm("assigned_to", event.target.value)}
                            />
                        </div>

                        <textarea
                            placeholder="Requested records, attachments, or files needed"
                            value={requestForm.requested_records}
                            onChange={(event) => updateRequestForm("requested_records", event.target.value)}
                        />
                        <textarea
                            placeholder="Reason for request"
                            value={requestForm.reason}
                            onChange={(event) => updateRequestForm("reason", event.target.value)}
                        />
                        <textarea
                            placeholder="Probable cause, operational summary, or context"
                            value={requestForm.summary}
                            onChange={(event) => updateRequestForm("summary", event.target.value)}
                        />

                        <button type="submit">Submit Request</button>
                    </form>

                    <section className="interagency-tracker">
                        <h2>Status Tracker</h2>

                        <div className="request-tracker-header">
                            <span>Request Type</span>
                            <span>Status</span>
                            <span>Assigned To</span>
                        </div>

                        {agencyRequests.length === 0 ? (
                            <p>No inter-agency requests submitted yet.</p>
                        ) : (
                            agencyRequests.slice(0, visibleRequestCount).map((request) => (
                                <article key={request.exchange_id} className="request-tracker-card">
                                    <button
                                        type="button"
                                        onClick={() =>
                                            setExpandedRequestId((currentId) =>
                                                currentId === request.exchange_id ? null : request.exchange_id
                                            )
                                        }
                                    >
                                        <span>{request.request_type || request.information_type}</span>
                                        <span>{statusLabels[request.status] || request.status}</span>
                                        <span>{request.assigned_to || `User ${request.approved_by}`}</span>
                                    </button>

                                    {expandedRequestId === request.exchange_id && (
                                        <div className="request-tracker-details">
                                            <p>Case: {request.case_id}</p>
                                            <p>{request.from_agency} to {request.to_agency}</p>
                                            <p>Subject: {request.subject || "Not recorded"}</p>
                                            <p>Authority: {request.legal_authority || "Not recorded"}</p>
                                            <p>Due: {request.due_date ? new Date(request.due_date).toLocaleString() : "Not set"}</p>
                                            <p>Delivery: {request.delivery_method || "Not recorded"}</p>
                                            <p>Records: {request.requested_records || request.summary}</p>
                                            <small>{request.audit_log || "Audit trail starts when this request is created."}</small>
                                        </div>
                                    )}
                                </article>
                            ))
                        )}

                        {agencyRequests.length > 2 && (
                            <div className="list-toggle-row">
                                {visibleRequestCount > 2 && (
                                    <button
                                        type="button"
                                        className="list-toggle-button"
                                        onClick={() => setVisibleRequestCount(2)}
                                    >
                                        Show fewer
                                    </button>
                                )}
                                {visibleRequestCount < agencyRequests.length && (
                                    <>
                                        <button
                                            type="button"
                                            className="list-toggle-button"
                                            onClick={() =>
                                                setVisibleRequestCount((current) =>
                                                    Math.min(current + 4, agencyRequests.length)
                                                )
                                            }
                                        >
                                            Show {Math.min(4, agencyRequests.length - visibleRequestCount)} more requests
                                        </button>
                                        <button
                                            type="button"
                                            className="list-toggle-button"
                                            onClick={() => setVisibleRequestCount(agencyRequests.length)}
                                        >
                                            Show all
                                        </button>
                                    </>
                                )}
                            </div>
                        )}
                    </section>
                </div>
            </section>

            <div className="agency-directory-layout">
                <section className="agency-search-panel">
                    <label htmlFor="agency-search">Find Agency</label>
                    <input
                        id="agency-search"
                        type="search"
                        placeholder="Search by agency, state, city, phone, or address"
                        value={agencySearch}
                        onChange={(event) => setAgencySearch(event.target.value)}
                    />
                    <span>
                        Showing {filteredAgencies.length} of {agencies.length} agencies
                    </span>
                </section>

                <section className="agency-directory-results">
                    {filteredAgencies.length === 0 ? (
                        <section className="agencies-panel">
                            <p>No agencies found.</p>
                        </section>
                    ) : (
                        <div className="agencies-grid">
                            {filteredAgencies.slice(0, visibleAgencyCount).map((agency) => (
                                <article key={agency.agency_id} className="agency-card">
                                    <div className="agency-card-topline">
                                        <button
                                            type="button"
                                            className="agency-name-button"
                                            onClick={() =>
                                                setExpandedAgencyId((currentId) =>
                                                    currentId === agency.agency_id ? null : agency.agency_id
                                                )
                                            }
                                            aria-expanded={expandedAgencyId === agency.agency_id}
                                        >
                                            {agency.agency_name}
                                        </button>
                                    </div>

                                    {expandedAgencyId === agency.agency_id && (
                                        <div className="agency-card-details">
                                            <p>Type: {agency.agency_type || "Not provided"}</p>
                                            <p>City: {agency.city || "Not provided"}</p>
                                            <p>State: {agency.state || "Not provided"}</p>
                                            <p>Phone: {agency.contact_phone || "Not provided"}</p>
                                            <p>Address: {agency.address || "Not provided"}</p>
                                            <p>ID: {agency.agency_id}</p>
                                            {agency.lifecycle_status && (
                                                <p>Status: <span className={`agency-lifecycle-status ${agency.lifecycle_status}`}>{agency.lifecycle_status}</span></p>
                                            )}
                                            {agency.status_changed_at && (
                                                <p>Last status change: {new Date(agency.status_changed_at).toLocaleString()}</p>
                                            )}
                                            {isPlatformAdmin && Number.isInteger(agency.agency_id) && agency.lifecycle_status !== "offboarded" && (
                                                <div className="agency-lifecycle-controls">
                                                    <label htmlFor={`agency-status-${agency.agency_id}`}>Lifecycle status</label>
                                                    <select
                                                        id={`agency-status-${agency.agency_id}`}
                                                        value={statusDrafts[agency.agency_id]?.status || agency.lifecycle_status || "active"}
                                                        onChange={(event) => updateLifecycleDraft(agency.agency_id, "status", event.target.value)}
                                                    >
                                                        <option value="active">Active</option>
                                                        <option value="suspended">Suspended</option>
                                                        <option value="offboarded">Offboarded (permanent)</option>
                                                    </select>
                                                    <textarea
                                                        aria-label={`Reason for changing ${agency.agency_name}`}
                                                        placeholder="Required operational reason (10+ characters)"
                                                        value={statusDrafts[agency.agency_id]?.reason || ""}
                                                        onChange={(event) => updateLifecycleDraft(agency.agency_id, "reason", event.target.value)}
                                                    />
                                                    <button
                                                        type="button"
                                                        disabled={lifecycleBusyId === agency.agency_id}
                                                        onClick={() => submitLifecycleChange(agency)}
                                                    >
                                                        {lifecycleBusyId === agency.agency_id ? "Updating..." : "Apply Status Change"}
                                                    </button>
                                                </div>
                                            )}
                                            {agency.website && (
                                                <a href={agency.website} target="_blank" rel="noreferrer">
                                                    Official Website
                                                </a>
                                            )}
                                        </div>
                                    )}
                                </article>
                            ))}
                            {filteredAgencies.length > 2 && (
                                <div className="list-toggle-row">
                                    {visibleAgencyCount > 2 && (
                                        <button
                                            type="button"
                                            className="list-toggle-button"
                                            onClick={() => setVisibleAgencyCount(2)}
                                        >
                                            Show fewer
                                        </button>
                                    )}
                                    {visibleAgencyCount < filteredAgencies.length && (
                                        <>
                                            <button
                                                type="button"
                                                className="list-toggle-button"
                                                onClick={() =>
                                                    setVisibleAgencyCount((current) =>
                                                        Math.min(current + 4, filteredAgencies.length)
                                                    )
                                                }
                                            >
                                                Show {Math.min(4, filteredAgencies.length - visibleAgencyCount)} more agencies
                                            </button>
                                            <button
                                                type="button"
                                                className="list-toggle-button"
                                                onClick={() => setVisibleAgencyCount(filteredAgencies.length)}
                                            >
                                                Show all
                                            </button>
                                        </>
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </section>
            </div>
        </div>
    );
}

export default AgencyManagement;
