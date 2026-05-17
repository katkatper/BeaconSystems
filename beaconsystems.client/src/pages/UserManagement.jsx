import React, { useEffect, useState } from "react";

function UserManagement() {
    const [users, setUsers] = useState([]);
    const [message, setMessage] = useState("");

    useEffect(() => {
        const token = localStorage.getItem("token");

        fetch("http://127.0.0.1:8000/admin/users/", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        })
            .then((res) => res.json())
            .then((data) => setUsers(data))
            .catch((err) => {
                console.error(err);
                setMessage("Could not load users.");
            });
    }, []);
    const promoteToInvestigator = async (userId) => {

        const token = localStorage.getItem("token");

        try {

            const response = await fetch(
                `http://127.0.0.1:8000/admin/users/${userId}/role?role=investigator`,
                {
                    method: "PUT",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                throw new Error("Could not update role");
            }

            window.location.reload();

        } catch (err) {

            console.error(err);

            setMessage("Failed to update role.");
        }
    };

    return (
        <div>
            <h1>User Management</h1>

            {message && <p>{message}</p>}

            {users.map((user) => (
                <div key={user.user_id}>
                    <h3>{user.username}</h3>
                    <p>Email: {user.email}</p>
                    <p>Role: {user.role}</p>
                    <p>Agency ID: {user.agency_id}</p>
                    <p>Status: {user.is_active ? "Active" : "Disabled"} <button
                        onClick={() => promoteToInvestigator(user.user_id)}
                    >
                        Make Investigator
                    </button></p>

                    <hr />
                </div>
            ))}
        </div>
    );
}

export default UserManagement;