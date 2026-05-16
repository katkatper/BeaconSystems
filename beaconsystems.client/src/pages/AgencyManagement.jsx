import React, { useState, useEffect } from 'react';



function AgencyManagement() {
    const [agencies, setAgencies] = useState([]);
    const [message, setMessage] = useState('');

    useEffect(() => {

        const token = localStorage.getItem('token');

        fetch('http://127.0.0.1:8000/agencies/', {
            headers: {
                'Authorization': `Bearer ${token}`
            },
        })
            .then((res) => res.json())
            .then((data) => setAgencies(data))
            .catch((err) => {
                console.error(err);
                setMessage("Could not load agencies.");

        });

    }, []);

    return (
        <div>
            <h1>Agency Management</h1>

            {message && <p>{message}</p>}

            {agencies.length === 0 ? (
                <p>No agencies found.</p>
            ) : (
                agencies.map((agency) => (
                    <div
                        key={agency.agency_id}
                        style={{
                            border: "1px solid gray",
                            padding: "12px",
                            margin: "10px",
                            borderRadius: "8px",
                        }}
                    >
                        <h3>{agency.agency_name}</h3>
                        <p>Type: {agency.agency_type}</p>
                        <p>City: {agency.city}</p>
                        <p>State: {agency.state}</p>
                        <p>Agency ID: {agency.agency_id}</p>
                    </div>
                ))
            )}
        </div>
    );
}

export default AgencyManagement;