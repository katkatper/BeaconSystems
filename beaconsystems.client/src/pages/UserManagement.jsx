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
            .then((res) => {
                if (!res.ok) {
                    throw new Error("Could not load users.");
                }

                return res.json();
            })
            .then((data) => {
                setUsers(Array.isArray(data) ? data : []);
                setMessage("");
            })
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
        <div className="users-page">
            <header className="users-header">
                <h1>User Management</h1>
                <p>Manage Beacon account status, roles, and investigator access.</p>
            </header>

            {message && <p className="alert-banner">{message}</p>}

            <section className="users-panel">
                <div className="users-panel-header">
                    <span>Accounts</span>
                    <strong>{users.length} users</strong>
                </div>

                <div className="users-list">
                    {users.length === 0 ? (
                        <p>No users found.</p>
                    ) : (
                        users.map((user) => (
                            <article key={user.user_id} className="user-card">
                                <div className="user-card-main">
                                    <div>
                                        <h2>{user.username}</h2>
                                        <p>{user.email}</p>
                                    </div>

                                    <span className={user.is_active ? "status-pill active" : "status-pill inactive"}>
                                        {user.is_active ? "Active" : "Disabled"}
                                    </span>
                                </div>

                                <dl className="user-details">
                                    <div>
                                        <dt>Role</dt>
                                        <dd>{user.role}</dd>
                                    </div>
                                    <div>
                                        <dt>Agency ID</dt>
                                        <dd>{user.agency_id || "Unassigned"}</dd>
                                    </div>
                                    <div>
                                        <dt>User ID</dt>
                                        <dd>{user.user_id}</dd>
                                    </div>
                                </dl>

                                <div className="user-actions">
                                    <button
                                        type="button"
                                        onClick={() => promoteToInvestigator(user.user_id)}
                                    >
                                        Make Investigator
                                    </button>
                                </div>
                            </article>
                        ))
                    )}
                </div>
            </section>
        </div>
    );
}

export default UserManagement;
