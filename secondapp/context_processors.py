# secondapp/context_processors.py

def user_person(request):
    """Logged-in user's memberships available in every template automatically."""
    person = None
    owned_persons = []
    memberships = []
    active_org = None
    active_username = None

    if request.user.is_authenticated:
        person = request.user.persons.first()

        if person:
            owned_persons = person.owned_persons.select_related("user").all()

            # all memberships across all orgs
            for owned_person in owned_persons:
                owned_person_memberships = (
                    owned_person.memberships
                    .select_related("organization", "organization__user")
                    .all()
                )
                memberships.extend(owned_person_memberships)

            # detect active org from URL
            resolver_match = request.resolver_match
            if resolver_match and "username" in resolver_match.kwargs:
                username = resolver_match.kwargs["username"]
                active_org = next(
                    (
                        m.organization
                        for m in memberships
                        if m.organization.user.username == username
                    ),
                    None
                )

        # if active user page is org or individual
        if active_org:
            active_username = active_org.user.username
        elif request.user:
            active_username = request.user.username

    return {
        "person": person,
        "owned_persons": owned_persons,
        "memberships": memberships,
        "active_org": active_org,
        "active_username": active_username,
    }
