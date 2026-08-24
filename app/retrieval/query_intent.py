def is_ambiguous_query(query: str) -> bool:

    ambiguous_queries = [
        "what is the limit",
        "what's the limit",
        "what is the policy",
        "what about that",
        "what are the rules"
    ]

    normalized = query.lower().strip().rstrip("?")

    return normalized in [
        q.rstrip("?")
        for q in ambiguous_queries
    ]


def detect_historical_intent(query: str) -> bool:

    query_lower = query.lower()

    historical_terms = [
        "2025",
        "2024",
        "previous",
        "older",
        "historical",
        "last year",
        "old pricing"
    ]

    return any(
        term in query_lower
        for term in historical_terms
    )


def detect_current_intent(query: str) -> bool:

    query_lower = query.lower()

    historical_terms = [
        "2025",
        "2024",
        "previous",
        "older",
        "historical",
        "last year",
        "old pricing"
    ]

    if any(
        term in query_lower
        for term in historical_terms
    ):
        return False

    explicit_current_terms = [
        "current",
        "latest",
        "currently",
        "active",
        "effective",
        "most recent"
    ]

    if any(
        term in query_lower
        for term in explicit_current_terms
    ):
        return True

    # Versioned subjects where current version
    # is the sensible default
    current_by_default_terms = [
        "orbitsuite",
        "pricing",
        "rate card"
    ]

    if any(
        term in query_lower
        for term in current_by_default_terms
    ):
        return True

    return False