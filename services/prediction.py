def predict_next_location(sightings):

    if not sightings:
        return "No data"

    last= sightings[-1]

    return f"Likely near{last.location}"



