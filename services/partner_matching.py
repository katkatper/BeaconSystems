from typing import Any


STOP_WORDS = {"the", "and", "for", "with", "near", "from"}


def normalize_text(value: Any) -> str:
    return "" if value is None else str(value).strip().lower()


def text_tokens(value: str) -> set[str]:
    normalized = "".join(
        character if character.isalnum() else " "
        for character in normalize_text(value)
    )
    return {
        token
        for token in normalized.split()
        if len(token) > 2 and token not in STOP_WORDS
    }


def split_subject_name(subject_name: str | None) -> tuple[str | None, str | None]:
    if not subject_name or not subject_name.strip():
        return None, None

    parts = subject_name.strip().split()
    return (parts[0], None) if len(parts) == 1 else (parts[0], " ".join(parts[1:]))


def _ages_match(partner_age: Any, person_age: Any) -> bool:
    if partner_age in (None, "") or person_age in (None, ""):
        return False
    try:
        return int(partner_age) == int(person_age)
    except (TypeError, ValueError):
        return False


def score_case_match(case: Any, intake: Any) -> tuple[int, list[str]]:
    """Score explainable intake-to-case similarities without database access."""
    person = case.person
    raw_data = intake.raw_data or {}
    score = 0
    reasons: list[str] = []

    subject = normalize_text(intake.subject_name)
    summary = normalize_text(intake.summary)
    location = normalize_text(intake.location)
    search_blob = " ".join([subject, summary, location, normalize_text(raw_data)])

    first_name = normalize_text(person.first_name if person else "")
    last_name = normalize_text(person.last_name if person else "")
    full_name = " ".join(part for part in [first_name, last_name] if part)
    if full_name and full_name in search_blob:
        score += 45
        reasons.append("full name matched")
    else:
        if first_name and first_name in search_blob:
            score += 18
            reasons.append("first name matched")
        if last_name and last_name in search_blob:
            score += 25
            reasons.append("last name matched")

    partner_age = raw_data.get("age") if isinstance(raw_data, dict) else None
    if person and _ages_match(partner_age, person.age):
        score += 12
        reasons.append("age matched")

    for label, value in [
        ("eye color", person.eye_color if person else None),
        ("hair color", person.hair_color if person else None),
        ("risk level", person.risk_level if person else None),
    ]:
        normalized_value = normalize_text(value)
        if normalized_value and normalized_value in search_blob:
            score += 8
            reasons.append(f"{label} matched")

    case_locations = " ".join(
        normalize_text(value)
        for value in [
            case.last_seen_location,
            person.last_seen_location if person else "",
        ]
    )
    if text_tokens(location).intersection(text_tokens(case_locations)):
        score += min(
            15,
            len(text_tokens(location).intersection(text_tokens(case_locations))) * 5,
        )
        reasons.append("location overlapped")

    case_context = " ".join(
        normalize_text(value)
        for value in [
            case.case_number,
            case.title,
            case.description,
            case.notes,
            person.description if person else "",
            person.scars if person else "",
            person.tattoos if person else "",
            person.medical_conditions if person else "",
        ]
    )
    keyword_overlap = text_tokens(summary).intersection(text_tokens(case_context))
    if keyword_overlap:
        score += min(20, len(keyword_overlap) * 4)
        reasons.append("description keywords overlapped")

    if normalize_text(case.case_status) in {"closed", "cold"}:
        reasons.append(f"{case.case_status.lower()} case considered")

    return min(score, 100), reasons
