function MissingPersonsList() {

    const persons = [
        { id: 1, name: "John Doe", age: 34, status: "Missing" },
        { id: 2, name: "Jane Smith", age: 28, status: "Found" },

    ];
    return (
        <div>
            <h2>Missing Persons List</h2>

            <ul>
                {persons.map((person) => (

                    <li> key={person.id}- {person.name}-{person.age}- Status: {person.status}
                    </li>
                ))}
            </ul>
        </div>
    );

}
export default MissingPersonsList;