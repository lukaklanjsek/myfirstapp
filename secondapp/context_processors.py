# secondapp/context_processors.py
from .models import Membership, Role
from django.db.models import Q

from .permissions import AccessControl


def user_person(request):
    """Logged-in user's memberships available in every template automatically."""
    context = {
        "person": None,
        "memberships": [],
        "url_username": None,
        "ADMIN_ROLE": Role.objects.get(id=Role.ADMIN),
        "MEMBER_ROLE": Role.objects.get(id=Role.MEMBER),
    }

    if not request.user.is_authenticated:
        return context

    person = request.user.persons.first()
    if not person:
        return context

    context["person"] = person

    # Get username from URL (which org page are we on)
    context["url_username"] = request.resolver_match.kwargs.get("username")

    # get all memberships for this user
    context["memberships"] = list(
        Membership.objects.filter(
            Q(user=request.user) |  # Direct memberships (personal user)
            Q(person__owner=person)  # Org memberships where user owns the person
        )
        .select_related("user", "person")
        .prefetch_related(
            "user__organizations",
            "person__person_role__role"
        )
    )
    # # --------------------------------- TEST PRINTS ----------------------------
    # print(f"Person: {context['person']}")
    # print(f"URL Username: {context['url_username']}")
    # # print(f"Memberships: {context['memberships']}")
    # print(f"Available keys: {context.keys()}")
    # print(f"\nMemberships ({len(context['memberships'])}):")
    #
    # for i, membership in enumerate(context['memberships']):
    #     print(f"\n  [{i}] User: {membership.user}")
    #     print(f"      Person: {membership.person}")
    #     print(f"      Person owner: {membership.person.owner}")
    #
    #     person_roles = membership.person.person_role.all()
    #     if person_roles:
    #         print(f"      Roles: {[pr.role.title for pr in person_roles]}")
    #     else:
    #         print(f"      Roles: None")
    #     print(person_roles)
    #     print(context["ADMIN_ROLE"])
    #     if context["ADMIN_ROLE"] in person_roles:
    #         print("hello")
    #
    #     # Check if this membership connects to an org
    #     if membership.user.organizations.exists():
    #         org = membership.user.organizations.first()
    #         print(f"      → Org: {org.name}")
    #     else:
    #         print(f"      → No org (personal membership)")

    return context
