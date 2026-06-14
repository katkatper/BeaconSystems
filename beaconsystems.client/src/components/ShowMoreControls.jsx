import React from "react";

function ShowMoreControls({
    total,
    visible,
    noun = "items",
    step = 4,
    minimum = 2,
    onShowMore,
    onShowAll,
    onShowFewer,
}) {
    if (total <= minimum) {
        return null;
    }

    const remaining = Math.max(total - visible, 0);

    return (
        <div className="list-toggle-row">
            {remaining > 0 ? (
                <>
                    <button
                        type="button"
                        className="list-toggle-button"
                        onClick={onShowMore}
                    >
                        Show {Math.min(step, remaining)} more {noun}
                    </button>
                    <button
                        type="button"
                        className="list-toggle-button"
                        onClick={onShowAll}
                    >
                        Show all
                    </button>
                </>
            ) : (
                <button
                    type="button"
                    className="list-toggle-button"
                    onClick={onShowFewer}
                >
                    Show fewer
                </button>
            )}
        </div>
    );
}

export default ShowMoreControls;
