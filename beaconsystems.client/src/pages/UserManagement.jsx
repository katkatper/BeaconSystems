import { apiUrl } from "../api.jsx";
import React, { useEffect, useState } from "react";

function UserManagement() {
    const [users, setUsers] = useState([]);
    const [visibleUserCount, setVisibleUserCount] = useState(2);
    const [managedUserCount, setManagedUserCount] = useState(2);
    const [message, setMessage] = useState("");
    const [userSearch, setUserSearch] = useState("");
    const [userRoleFilter, setUserRoleFilter] = useState("all");
    const [userStatusFilter, setUserStatusFilter] = useState("active");
    const [resetPasswords, setResetPasswords] = useState({});
    const [newUser, setNewUser] = useState({
        username: "",
        email: "",
        password: "",
        role: "investigator",
        agency_id: "",
    });
    const token = localStorage.getItem("token");
    const currentRole = localStorage.getItem("role") || "viewer";
    const roleOptions = currentRole === "admin"
        ? [
            ["investigator", "Investigator"],
            ["supervisor", "Supervisor"],
            ["analyst", "Analyst"],
            ["viewer", "Viewer"],
            ["agency_admin", "Agency Admin"],
            ["admin", "Admin"],
        ]
        : [
            ["investigator", "Investigator"],
            ["supervisor", "Supervisor"],
            ["analyst", "Analyst"],
            ["viewer", "Viewer"],
        ];
    const filteredUsers = users.filter((user) => {
        const searchText = `${user.username || ""} ${user.email || ""} ${user.role || ""}`.toLowerCase();
        const matchesSearch = searchText.includes(userSearch.trim().toLowerCase());
        const matchesRole = userRoleFilter === "all" || user.role === userRoleFilter;
        const matchesStatus =
            userStatusFilter === "all" ||
            (userStatusFilter === "active" && user.is_active) ||
            (userStatusFilter === "disabled" && !user.is_active);

        return matchesSearch && matchesRole && matchesStatus;
    });
    const canManageUser = (user) => currentRole !== "supervisor" ||
        !["admin", "agency_admin"].includes(user.role);
    const getApiErrorMessage = (errorData, fallback) => {
        if (Array.isArray(errorData.detail)) {
            return errorData.detail
                .map((item) => `${item.loc?.slice(1).join(".") || "field"}: ${item.msg}`)
                .join("; ");
        }

        return errorData.detail || fallback;
    };

    useEffect(() => {
        fetch(apiUrl("/admin/users/"), {
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
    }, [token]);

    const registerUser = async (event) => {
        event.preventDefault();

        try {
            const payload = {
                username: newUser.username.trim(),
                email: newUser.email.trim(),
                password: newUser.password,
                role: newUser.role,
                agency_id: newUser.agency_id ? Number(newUser.agency_id) : null,
            };

            const response = await fetch(apiUrl("/admin/users/"), {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(getApiErrorMessage(errorData, "Could not register user"));
            }

            const data = await response.json();
            setUsers((currentUsers) => [...currentUsers, data].sort((a, b) =>
                (a.username || "").localeCompare(b.username || "")
            ));
            setNewUser({
                username: "",
                email: "",
                password: "",
                role: "investigator",
                agency_id: "",
            });
            setMessage(`${data.username} was registered as ${data.role}.`);
        } catch (err) {
            console.error(err);
            setMessage(err.message || "Could not register user.");
        }
    };

    const updateUserStatus = async (userId, isActive) => {
        try {
            const response = await fetch(
                apiUrl(`/admin/users/${userId}/status?is_active=${isActive}`),
                {
                    method: "PUT",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Could not update user status");
            }

            setUsers((currentUsers) =>
                currentUsers.map((user) =>
                    user.user_id === userId ? { ...user, is_active: isActive } : user
                )
            );
            setMessage(isActive ? "User reactivated." : "User disabled and archived from active work.");
        } catch (err) {
            console.error(err);
            setMessage(err.message || "Could not update user status.");
        }
    };

    const resetUserPassword = async (userId) => {
        const temporaryPassword = resetPasswords[userId] || "";

        try {
            const response = await fetch(
                apiUrl(`/admin/users/${userId}/reset-password`),
                {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({
                        temporary_password: temporaryPassword,
                    }),
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(getApiErrorMessage(errorData, "Could not reset user password"));
            }

            const data = await response.json();
            setResetPasswords((currentPasswords) => ({
                ...currentPasswords,
                [userId]: "",
            }));
            setMessage(`${data.message}. They must change it on next login.`);
        } catch (err) {
            console.error(err);
            setMessage(err.message || "Could not reset user password.");
        }
    };

    const promoteToInvestigator = async (userId) => {
        try {
            const response = await fetch(
                apiUrl(`/admin/users/${userId}/role?role=investigator`),
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

            setUsers((currentUsers) =>
                currentUsers.map((user) =>
                    user.user_id === userId ? { ...user, role: "investigator" } : user
                )
            );
            setMessage("User role updated to investigator.");

        } catch (err) {

            console.error(err);

            setMessage("Failed to update role.");
        }
    };

    return (
        <div className="users-page">
            <header className="users-header">
                <h1>User Management</h1>
            </header>

            {message && <p className="alert-banner">{message}</p>}

            <section className="users-admin-grid">
                <section className="users-panel user-admin-panel">
                    <div className="users-panel-header">
                        <span>User Access</span>
                        <strong>Register New User</strong>
                    </div>

                    <form className="supervisor-user-form" onSubmit={registerUser}>
                        <input
                            type="text"
                            placeholder="Username"
                            value={newUser.username}
                            onChange={(event) =>
                                setNewUser((current) => ({ ...current, username: event.target.value }))
                            }
                            required
                        />

                        <input
                            type="email"
                            placeholder="Email"
                            value={newUser.email}
                            onChange={(event) =>
                                setNewUser((current) => ({ ...current, email: event.target.value }))
                            }
                            required
                        />

                        <input
                            type="password"
                            placeholder="Temporary password"
                            value={newUser.password}
                            onChange={(event) =>
                                setNewUser((current) => ({ ...current, password: event.target.value }))
                            }
                            required
                        />

                        <select
                            value={newUser.role}
                            onChange={(event) =>
                                setNewUser((current) => ({ ...current, role: event.target.value }))
                            }
                        >
                            {roleOptions.map(([value, label]) => (
                                <option key={value} value={value}>{label}</option>
                            ))}
                        </select>

                        {currentRole === "admin" && (
                            <input
                                type="number"
                                min="1"
                                placeholder="Agency ID"
                                value={newUser.agency_id}
                                onChange={(event) =>
                                    setNewUser((current) => ({ ...current, agency_id: event.target.value }))
                                }
                            />
                        )}

                        <button type="submit">Register User</button>
                    </form>
                </section>

                <section className="users-panel user-admin-panel">
                    <div className="users-panel-header">
                        <span>User Access</span>
                        <strong>Disable or Restore Users</strong>
                    </div>

                    <div className="supervisor-user-filters">
                        <input
                            type="search"
                            placeholder="Search users"
                            value={userSearch}
                            onChange={(event) => setUserSearch(event.target.value)}
                        />

                        <select
                            value={userRoleFilter}
                            onChange={(event) => setUserRoleFilter(event.target.value)}
                        >
                            <option value="all">All roles</option>
                            {roleOptions.map(([value, label]) => (
                                <option key={value} value={value}>{label}</option>
                            ))}
                        </select>

                        <select
                            value={userStatusFilter}
                            onChange={(event) => setUserStatusFilter(event.target.value)}
                        >
                            <option value="active">Active</option>
                            <option value="disabled">Disabled</option>
                            <option value="all">All statuses</option>
                        </select>
                    </div>

                    <div className="supervisor-user-list">
                        {filteredUsers.length === 0 ? (
                            <p>No users found.</p>
                        ) : (
                            filteredUsers.slice(0, managedUserCount).map((user) => (
                                <article key={user.user_id} className="queue-item">
                                    <div>
                                        <strong>{user.username}</strong>
                                        <span>{user.is_active ? "active" : "disabled"}</span>
                                    </div>
                                    <p>{user.email}</p>
                                    <p>{user.role} | Agency {user.agency_id || "Unassigned"}</p>
                                    <button
                                        type="button"
                                        disabled={!canManageUser(user)}
                                        onClick={() => updateUserStatus(user.user_id, !user.is_active)}
                                    >
                                        {user.is_active ? "Disable / Archive" : "Restore User"}
                                    </button>
                                    <div className="supervisor-password-reset">
                                        <input
                                            type="password"
                                            placeholder="Temporary password (12+ chars)"
                                            value={resetPasswords[user.user_id] || ""}
                                            onChange={(event) =>
                                                setResetPasswords((currentPasswords) => ({
                                                    ...currentPasswords,
                                                    [user.user_id]: event.target.value,
                                                }))
                                            }
                                        />
                                        <button
                                            type="button"
                                            disabled={!canManageUser(user)}
                                            onClick={() => resetUserPassword(user.user_id)}
                                        >
                                            Reset Password
                                        </button>
                                    </div>
                                </article>
                            ))
                        )}
                        {filteredUsers.length > 2 && (
                            <div className="list-toggle-row">
                                {managedUserCount > 2 && (
                                    <button
                                        type="button"
                                        className="list-toggle-button"
                                        onClick={() => setManagedUserCount(2)}
                                    >
                                        Show fewer
                                    </button>
                                )}
                                {managedUserCount < filteredUsers.length && (
                                    <>
                                        <button
                                            type="button"
                                            className="list-toggle-button"
                                            onClick={() =>
                                                setManagedUserCount((current) =>
                                                    Math.min(current + 4, filteredUsers.length)
                                                )
                                            }
                                        >
                                            Show {Math.min(4, filteredUsers.length - managedUserCount)} more users
                                        </button>
                                        <button
                                            type="button"
                                            className="list-toggle-button"
                                            onClick={() => setManagedUserCount(filteredUsers.length)}
                                        >
                                            Show all
                                        </button>
                                    </>
                                )}
                            </div>
                        )}
                    </div>
                </section>
            </section>

            <section className="users-panel">
                <div className="users-panel-header">
                    <span>Accounts</span>
                    <strong>{users.length} users</strong>
                </div>

                <div className="users-list">
                    {users.length === 0 ? (
                        <p>No users found.</p>
                    ) : (
                        users.slice(0, visibleUserCount).map((user) => (
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
                    {users.length > 2 && (
                        <div className="list-toggle-row">
                            {visibleUserCount > 2 && (
                                <button
                                    type="button"
                                    className="list-toggle-button"
                                    onClick={() => setVisibleUserCount(2)}
                                >
                                    Show fewer
                                </button>
                            )}
                            {visibleUserCount < users.length && (
                                <>
                                    <button
                                        type="button"
                                        className="list-toggle-button"
                                        onClick={() =>
                                            setVisibleUserCount((current) =>
                                                Math.min(current + 4, users.length)
                                            )
                                        }
                                    >
                                        Show {Math.min(4, users.length - visibleUserCount)} more users
                                    </button>
                                    <button
                                        type="button"
                                        className="list-toggle-button"
                                        onClick={() => setVisibleUserCount(users.length)}
                                    >
                                        Show all
                                    </button>
                                </>
                            )}
                        </div>
                    )}
                </div>
            </section>
        </div>
    );
}

export default UserManagement;
