# secondapp/context_processors.py
from .models import Membership, Role
from django.db.models import Q

from .permissions import AccessControl


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
            Q(user=request.user) |  # Direct memberships (personal user)
            Q(person__owner=person)  # Org memberships where user owns the person
        )
        .select_related("user", "person")
        .order_by("user__username")
    )

    # Get username from URL (which org page are we on)
    # context["owner_username"] =

    context["ADMIN_ROLE"] = Role.ADMIN
    context["MEMBER_ROLE"] = Role.MEMBER

    return context
