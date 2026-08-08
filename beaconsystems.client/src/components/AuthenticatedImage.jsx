import React, { useEffect, useState } from "react";
import { API_BASE, apiBlob } from "../api.jsx";


function AuthenticatedImage({ src, alt, ...props }) {
    const [resolvedSrc, setResolvedSrc] = useState("");
    const isBeaconPhoto = Boolean(src) && (
        src.startsWith(`${API_BASE}/persons/photo/`) ||
        src.startsWith("/persons/photo/")
    );

    useEffect(() => {
        if (!src || !isBeaconPhoto) {
            return undefined;
        }

        let objectUrl = "";
        let isMounted = true;

        apiBlob(src)
            .then((blob) => {
                if (!isMounted) {
                    return;
                }

                objectUrl = URL.createObjectURL(blob);
                setResolvedSrc(objectUrl);
            })
            .catch((error) => {
                console.error("Could not load protected person photo", error);
                if (isMounted) {
                    setResolvedSrc("");
                }
            });

        return () => {
            isMounted = false;
            if (objectUrl) {
                URL.revokeObjectURL(objectUrl);
            }
        };
    }, [isBeaconPhoto, src]);

    if (!src) {
        return null;
    }

    if (isBeaconPhoto && !resolvedSrc) {
        return <div className="protected-image-placeholder" role="img" aria-label={`${alt} loading`} />;
    }

    return <img src={isBeaconPhoto ? resolvedSrc : src} alt={alt} {...props} />;
}

export default AuthenticatedImage;
