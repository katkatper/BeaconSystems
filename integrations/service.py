from .client import fetch_Beacon_systems

def get_police_missing_cases():
    data= fetch_Beacon_systems()

    #Clean and standarized data

    formatted=[]
    for person in data:
        formatted.append({
            "name":person.get("name"),
            "last_seen": person.get("last_seen"),
            "source": "police"
            })
        return formatted

