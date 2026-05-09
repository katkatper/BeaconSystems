def calculate_match_score(person, record):
    score = 0

    if person.first_name and record.first_name:
        if person.first_name.lower() == record.first_name.lower():
            score += 30

    if person.last_name and record.last_name:
        if person.last_name.lower() == record.last_name.lower():
            score += 30

    if person.age and record.age:
        if person.age == record.age:
            score += 20

    if person.last_seen_location and record.location:
        if person.last_seen_location.lower() in record.location.lower():
            score += 20

    return score
