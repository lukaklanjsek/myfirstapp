# secondapp/context_processors.py
from .models import Membership, Role


def user_person(request):
    """Logged-in user's memberships available in every template automatically."""
    context = {
        "person": None,
        "memberships": [],
        "owner_username": None,
    }

    if not request.user.is_authenticated:
        return context

    person = request.user.persons.first()
    if not person:
        return context

    context["person"] = person

    # get all memberships for this user
    context["memberships"] = list(
        Membership.objects.filter(
            person__owner=person
        )
        .select_related("user", "person", "role")
        .order_by("user__username", "role__id")
    )

    # Get username from URL (which org page are we on)
    context["owner_username"] = (
        request.resolver_match.kwargs.get('username')
        if request.resolver_match else None
    ) or request.user.username

    context["ADMIN_ROLE"] = Role.ADMIN
    context["MEMBER_ROLE"] = Role.MEMBER

    return context
