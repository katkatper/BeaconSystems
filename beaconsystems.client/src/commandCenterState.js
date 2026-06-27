const READ_STATE_EVENT = "beacon-command-read-state-changed";

const getUserScope = () => {
    const username = localStorage.getItem("username") || "anonymous";
    const role = localStorage.getItem("role") || "viewer";
    return `${role}:${username}`;
};

export const getReadStateKey = (collection) => `beacon:${getUserScope()}:${collection}:viewed`;

export const readViewedIds = (collection) => {
    try {
        return JSON.parse(localStorage.getItem(getReadStateKey(collection)) || "[]");
    } catch {
        return [];
    }
};

export const hasViewedItem = (collection, itemId) => readViewedIds(collection).includes(itemId);

export const markItemViewed = (collection, itemId) => {
    const viewed = new Set(readViewedIds(collection));
    viewed.add(itemId);
    localStorage.setItem(getReadStateKey(collection), JSON.stringify([...viewed]));
    window.dispatchEvent(new CustomEvent(READ_STATE_EVENT, { detail: { collection, itemId } }));
};

export const subscribeToReadState = (callback) => {
    window.addEventListener(READ_STATE_EVENT, callback);
    window.addEventListener("storage", callback);

    return () => {
        window.removeEventListener(READ_STATE_EVENT, callback);
        window.removeEventListener("storage", callback);
    };
};

export const getUnviewedCount = (collection, items) => {
    const viewed = new Set(readViewedIds(collection));
    return items.reduce((total, item) => {
        if (viewed.has(item.id)) return total;
        return total + Math.max(Number(item.count || 0), 0);
    }, 0);
};

export const getVisibleCount = (collection, item) => (
    hasViewedItem(collection, item.id) ? 0 : Math.max(Number(item.count || 0), 0)
);
