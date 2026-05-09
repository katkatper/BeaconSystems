import React, { useEffect, useState } from "react";

function ExternalRecordList() {
    const [records, setRecords] = useState([]);

    useEffect(() => {
        fetch("http://127.0.0.1:8000/external-records/")
            .then((res) => res.json())
            .then((data) => setRecords(data));
    }, []);

    return (
        <div>
            <h2>External Records</h2>

            <table border="1">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Type</th>
                        <th>Name</th>
                        <th>Age</th>
                        <th>Location</th>
                        <th>Notes</th>
                    </tr>
                </thead>

                <tbody>
                    {records.map((r) => (
                        <tr key={r.id}>
                            <td>{r.id}</td>
                            <td>{r.record_type}</td>
                            <td>{r.first_name} {r.last_name}</td>
                            <td>{r.age}</td>
                            <td>{r.location}</td>
                            <td>{r.notes}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default ExternalRecordList;