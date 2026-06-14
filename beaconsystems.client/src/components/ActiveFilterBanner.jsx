import React from "react";

function ActiveFilterBanner({ children, compact = false, onClear }) {
    return (
        <div className={`active-filter-banner ${compact ? "compact" : ""}`}>
            <span>{children}</span>
            {onClear && (
                <button type="button" onClick={onClear}>
                    Clear filter
                </button>
            )}
        </div>
    );
}

export default ActiveFilterBanner;
