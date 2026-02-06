# secondapp/context_processors.py

def user_person(request):
    """Logged-in user's memberships available in every template automatically."""
    person = None
    owned_persons = []
    memberships = []
    active_org = None

    if request.user.is_authenticated:
        person = request.user.persons.first()

        if person:
            owned_persons = person.owned_persons.select_related("user").all()

            for owned_person in owned_persons:
                owned_person_memberships = (
                    owned_person.memberships
                    .select_related("organization", "organization__user")
                    .all()
                )
                memberships.extend(owned_person_memberships)


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
        "owned_persons": owned_persons,
        "memberships": memberships,
        "active_org": active_org,
    }
