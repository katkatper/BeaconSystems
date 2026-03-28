import React, { useState } from "react";

function AddPerson() {
    const [name, setName] = useState("");
    const [age, setAge] = useState("");

    const handleSubmit = (e) => {

        e.preventDefault();
        console.log({ name, age });

    };

    return (

        <div>
            <h2> Add Missing Person report</h2>

            <form>
                onSubmit={handleSubmit}>

                <input
                    type="text"
                    placeholder="Name"
                    onChange={(e) => setName(e.target.value)}

                />

                <input
                    type="number"
                    placeholder="Age"
                    onChange={(e) => setAge(e.target.value)}

                />

                    <button> type="submit">Submit</button>  
                  
                   
            </form>

        </div >

    );

}
export default AddPerson





