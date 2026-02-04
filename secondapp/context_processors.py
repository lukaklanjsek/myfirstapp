# secondapp/context_processors.py

def user_person(request):
    """Logged-in user's memberships available in every template automatically."""
    person = None
    memberships = []
    active_org = None

    if request.user.is_authenticated:
        person = request.user.persons.first()
        if person:
            memberships = (
                person.memberships
                .select_related("organization", "organization__user")
                .all()
            )

            # detect active org from URL
            resolver_match = request.resolver_match
            if resolver_match and "org_username" in resolver_match.kwargs:
                org_username = resolver_match.kwargs["org_username"]
                active_org = next(
                    (
                        m.organization
                        for m in memberships
                        if m.organization.user.username == org_username
                    ),
                    None
                )

    return {
        "person": person,
        "memberships": memberships,
        "active_org": active_org,
    }
