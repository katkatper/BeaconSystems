import React from "react";

function MissingPersonsList() {
    const people = [
        { id: 1, name: "John Doe", age: 34, status: "Missing" },
        { id: 2, name: "Jane Smith", age: 28, status: "Found" },
    ];

    return (
        <div>
            <h1>Missing Persons List</h1>

            <ul>
                {people.map((person) => (
                    <li key={person.id}>
                        {person.name} - {person.age} - Status: {person.status}
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default MissingPersonsList;