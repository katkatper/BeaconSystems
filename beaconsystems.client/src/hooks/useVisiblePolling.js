import { useEffect, useRef } from "react";


export function useVisiblePolling(callback, intervalMs, enabled = true) {
    const callbackRef = useRef(callback);

    useEffect(() => {
        callbackRef.current = callback;
    }, [callback]);

    useEffect(() => {
        if (!enabled) return undefined;

        let cancelled = false;
        let inFlight = false;
        let timerId;

        const isActive = () => !cancelled;
        const run = async () => {
            if (cancelled || document.hidden || inFlight) return;

            inFlight = true;
            try {
                await callbackRef.current(isActive);
            } finally {
                inFlight = false;
            }
        };

        const schedule = () => {
            timerId = window.setTimeout(async () => {
                await run();
                if (!cancelled) schedule();
            }, intervalMs);
        };

        const onVisibilityChange = () => {
            if (!document.hidden) void run();
        };

        void run();
        schedule();
        document.addEventListener("visibilitychange", onVisibilityChange);

        return () => {
            cancelled = true;
            window.clearTimeout(timerId);
            document.removeEventListener("visibilitychange", onVisibilityChange);
        };
    }, [enabled, intervalMs]);
}
