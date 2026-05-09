def build_timeline(case, sightings):

    timeline=[]

    for s in sightings:

        timeline.append({
            "type": "sighting",
            "location": s.location,
            "time": s.created_at
            
            })

        return sorted(timeline, key=lambda x: x["time"])



