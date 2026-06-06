import React, { useState, useEffect } from "react";


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


function AgencyManagement() {
    const [agencies, setAgencies] = useState([]);
    const [message, setMessage] = useState("");
    const [expandedAgencyId, setExpandedAgencyId] = useState(null);
    const [agencySearch, setAgencySearch] = useState("");
    const [visibleAgencyCount, setVisibleAgencyCount] = useState(2);

    const token = localStorage.getItem("token");

    useEffect(() => {
        let isMounted = true;

        const loadAgencies = async () => {
            try {
                const response = await fetch("http://127.0.0.1:8000/agencies/", {
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
        </div>
    );
}

export default AgencyManagement;
