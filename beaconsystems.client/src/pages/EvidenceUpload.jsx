import React, { useState } from "react";



function EvidenceUpload() {

    const [caseId, setCaseId] = useState("");
    const [evidenceType, setEvidenceType] = useState("");
    const [description, setDescription] = useState("");
    const [file, setFile] = useState(null);

    const [message, setMessage] = useState("");

    const submitEvidence = async (e) => {

        e.preventDefault();

        const token = localStorage.getItem("token");

        const formData = new FormData();

        formData.append("case_id", caseId);
        formData.append("evidence_type", evidenceType);
        formData.append("description", description);
        formData.append("file", file);

        try {

            const response = await fetch(
                "http://127.0.0.1:8000/evidence/upload",
                {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                    body: formData,
                }
            );

            if (!response.ok) {
                throw new Error("Upload failed");
            }

            const data = await response.json();

            setMessage(data.message);

        } catch (err) {

            console.error(err);

            setMessage("Could not upload evidence.");
        }
    };

    return (
        <div>

            <h1>Upload Evidence</h1>

            <form onSubmit={submitEvidence}>

                <div>
                    <input
                        type="number"
                        placeholder="Case ID"
                        value={caseId}
                        onChange={(e) => setCaseId(e.target.value)}
                    />
                </div>

                <div>
                    <input
                        type="text"
                        placeholder="Evidence Type"
                        value={evidenceType}
                        onChange={(e) =>
                            setEvidenceType(e.target.value)
                        }
                    />
                </div>

                <div>
                    <textarea
                        placeholder="Description"
                        value={description}
                        onChange={(e) =>
                            setDescription(e.target.value)
                        }
                    />
                </div>

                <div>
                    <input
                        type="file"
                        onChange={(e) =>
                            setFile(e.target.files[0])
                        }
                    />
                </div>

                <button type="submit">
                    Upload Evidence
                </button>

            </form>

            {message && <p>{message}</p>}

        </div>
    );
}

export default EvidenceUpload;