# permissions.py

from django.core.exceptions import PermissionDenied
from django.db.models import Q
from .models import Organization, Role, Person, CustomUser, Membership, Song


class AccessControl:
    """
    Centralized access control for the application.
    All permission checks go through this class.
    """

    # centralized list of rights
    ROLE_PERMISSIONS = {
        Role.ADMIN: {"view", "create", "update", "delete"},
        Role.MEMBER: {"view"},
        Role.SUPPORTER: set(),
        Role.EXTERNAL: set(),
    }

    @classmethod
    def _user_memberships(cls, auth_user):
        if not auth_user.is_authenticated:
            return Membership.objects.none()

        return (Membership.objects
            .filter(
                Q(person__user=auth_user) |
                Q(person__owner__user=auth_user)
            ).select_related("organization", "role", "person")
        )

    @classmethod
    def get_user_role_in_org(cls, auth_user, organization):
        membership = (
            cls._user_memberships(auth_user)
            .filter(organization=organization)
            .first()
        )
        return membership.role if membership else None

    @classmethod
    def get_user_accessible_orgs(cls, auth_user):
        return Organization.objects.filter(
            id__in=cls._user_memberships(auth_user)
            .values_list("organization_id", flat=True)
        )

    @classmethod
    def filter_queryset_by_org(cls, auth_user, queryset):
        org_ids = cls._user_memberships(auth_user) \
            .values_list("organization_id", flat=True)

        return queryset.filter(
            organization_id__in=org_ids
        ).distinct()

    @classmethod
    def has_permission(cls, auth_user, action, organization=None):
        """
        Check if an auth user has permission for an action.
        If organization is provided, checks role within that org.
        If no organization, checks general permissions (for non-org resources).
        """
        membership = (
            cls._user_memberships(auth_user)
            .filter(organization=organization)
            .first()
        )

        if not membership:
            return False

        return action in cls.ROLE_PERMISSIONS.get(membership.role_id, set())

    @classmethod
    def get_viewable_people_queryset(cls, auth_user):
        return Person.objects.filter(
            memberships__in=cls._user_memberships(auth_user)
        ).distinct()

    @classmethod
    def can_access(cls, auth_user, action, organization=None,  queryset=None):
        """Does the user have permission for action and filter queryset if given."""
        if not cls.has_permission(auth_user, action, organization):
            return False, queryset.none() if queryset is not None else None

        if queryset is not None:
            return True, cls.filter_queryset_by_org(auth_user, queryset)
        return True, None

    @classmethod
    def filter_person_details(cls, auth_user, person, organization):
        """
        Filter person details based on the viewer's role in the same organization.
        Returns a dictionary with only the fields the user is allowed to see.
        For MEMBERS:
        - Show basic info (name, skills)
        - Hide sensitive contact info (email, phone)
        For ADMINS:
        - Show all information
        For others:
        - Return None
        """
        membership = (
            cls._user_memberships(auth_user)
            .filter(
                organization=organization,
                person=person
            )
            .select_related("role")
            .first()
        )

        if not membership:
            return None

        base_data = {
            "first_name": person.first_name,
            "last_name": person.last_name,
            "skills": person.skills.values_list("title", flat=True),
            "role_in_org": membership.role.title,
        }

        if membership.role_id == Role.ADMIN:
            return {
                **base_data,
                "email": person.email,
                "phone": person.phone,
                "address": person.address,
                "birth_date": person.birth_date,
                "created_at": person.created_at,
                "updated_at": person.updated_at,
            }

        if membership.role_id == Role.MEMBER:
            return base_data

        return None

    @classmethod
    def get_visible_members(cls, auth_user, organization):
        viewer_role = cls.get_user_role_in_org(auth_user, organization)

        if not viewer_role:
            return Membership.objects.none()

        memberships = (
            Membership.objects
            .filter(organization=organization)
            .select_related("person", "role")
        )

        if viewer_role.id == Role.ADMIN:
            return memberships

        if viewer_role.id == Role.MEMBER:
            return memberships.filter(role_id__in=[Role.ADMIN, Role.MEMBER])

        if viewer_role.id == Role.SUPPORTER:
            return memberships.filter(role_id=Role.ADMIN)

        return Membership.objects.none()

    @classmethod
    def can_view_song(cls, auth_user, song):
        """
        Admin + Member lahko vidi pesmi.
        Supporter/External ne.
        Handles both organizational or individual song owners.
        """
        if not auth_user.is_authenticated:
            return False

        owner_user = song.user

        # org is owner
        if hasattr(owner_user, "organizations"):  # organization user
            org = owner_user.organizations.first()  # only one
            if org:
                memberships = cls._user_memberships(auth_user).filter(
                    organization=org,
                    role_id__in=[Role.ADMIN, Role.MEMBER]
                )
                return memberships.exists()

        # owner is individual
        if owner_user == auth_user:
            return True

        return False

    @classmethod
    def can_view_song_list(cls, auth_user, owner_user):
        """
        Return queryset of Songs that auth_user can view:
        - Personal songs if owner_user is same as auth_user
        - Or org songs if auth_user is ADMIN or MEMBER of that org
        """
        if not auth_user.is_authenticated:
            return Song.objects.none()

        # personal songs
        if owner_user == auth_user:
            return Song.objects.filter(user=auth_user)

        # org songs
        org = Organization.objects.filter(user=owner_user).first()
        if not org:
            return Song.objects.none()

        memberships = cls._user_memberships(auth_user).filter(
            organization=org,
            role_id__in=[Role.ADMIN, Role.MEMBER]
        )
        if not memberships.exists():
            return Song.objects.none()

        return Song.objects.filter(user=org.user)

    @classmethod
    def can_manage_song(cls, auth_user, owner_user):
        """
        Returns True if auth_user can create/update/delete songs for owner_user.
        Rules:
        - Personal songs: owner_user == auth_user
        - Org songs: auth_user must be ADMIN in the org
        """
        if not auth_user.is_authenticated:
            return False

        # Personal songs
        if not hasattr(owner_user, "organizations") or not owner_user.organizations.exists():
            return auth_user == owner_user

        # Organizational songs
        organization = owner_user.organizations.first()
        is_admin = Membership.objects.filter(
            organization=organization,
            person__owner__user=auth_user,
            role_id=Role.ADMIN
        ).exists()

        return is_admin



        # if not auth_user.is_authenticated:
        #     return None
        #
        # # Get the organization this person belongs to
        # try:
        #     membership = person.memberships.filter(organization=organization).first()
        #     if not membership:
        #         return {"error": "Person has no active membership"}
        #
        #     org = membership.organization
        #     viewer_role = cls.get_user_role_in_org(auth_user, org)
        #
        #     if not viewer_role:
        #         return None
        #
        #     # Base data that everyone can see (if they have any access)
        #     base_data = {
        #         'first_name': person.first_name,
        #         'last_name': person.last_name,
        #         'skills': person.skills.values('title'),
        #         'role_in_org': membership.role.title
        #     }
        #
        #     # ADMINS get everything
        #     if viewer_role.id == Role.ADMIN:
        #         full_data = {
        #             **base_data,
        #             'email': person.email,
        #             'phone': person.phone,
        #             'address': person.address,
        #             'birth_date': person.birth_date,
        #             'created_at': person.created_at,
        #             'updated_at': person.updated_at
        #         }
        #         return full_data
        #
        #     # MEMBERS get basic info (no sensitive contact details)
        #     elif viewer_role.id == Role.MEMBER:
        #         return base_data
        #
        #     # SUPPORTER/EXTERNAL get minimal info
        #     else:
        #         return None # {
        #         #     'first_name': person.first_name,
        #         #     'last_name': person.last_name,
        #         #     'role_in_org': membership.role.title
        #         # }
        #
        # except Exception as e:
        #     # Log the error and return minimal info on failure
        #     print(f"Error filtering person details: {str(e)}")
        #     return {"error": "Access denied or invalid request"}



        #
        # if not role:
        #     return False
        #
        # return action in cls.ROLE_PERMISSIONS.get(role.id, set())

    # @classmethod
    # def filter_queryset_by_org(cls, auth_user, queryset):
    #     """
    #     Filter a queryset to only include items from organizations where the user has access.
    #     """
    #     if not auth_user.is_authenticated:
    #         return queryset.none()
    #
    #     # Get all organizations this auth user has membership in (through any person)
    #     org_ids = Organization.objects.filter(
    #         Q(memberships__person__user=auth_user) |
    #         Q(memberships__person__owner__user=auth_user)
    #     ).values_list('id', flat=True)
    #
    #     return queryset.filter(organization_id__in=org_ids).distinct()

    #
    # @classmethod
    # def get_user_role_in_org(cls, auth_user, organization):
    #     """
    #     Get the role of an auth user in a specific organization.
    #     AuthUser -> Person -> Membership -> Organization -> Role
    #     """
    #     if not auth_user.is_authenticated:
    #         return None
    #
    #     # Get the auth user's persons (usually one primary person)
    #     membership = (
    #         Membership.objects
    #         .filter(
    #             organization=organization
    #         )
    #         .filter(
    #             Q(person__user=auth_user) |
    #             Q(person__owner__user=auth_user)
    #         )
    #         .select_related("role")
    #     )
    #
    #     return membership.role if membership else None

    # @classmethod
    # def get_user_accessible_orgs(cls, auth_user):
    #     if not auth_user.is_authenticated:
    #         return Organization.objects.none()
    #
    #     return (
    #         Organization.objects
    #         .filter(
    #             Q(memberships__person__user=auth_user) |
    #             Q(memberships__person__owner__user=auth_user)
    #         )
    #         .distinct()
    #     )

    # @classmethod
    # def get_viewable_people_queryset(cls, user):
    #     org_ids = cls.get_user_accessible_orgs(user).values_list("id", flat=True)
    #
    #     return Person.objects.filter(
    #         memberships__organization_id__in=org_ids
    #     ).distinct()

    # # SONG ACCESS METHODS
    # @staticmethod
    # def can_view_song(user, song):
    #     """
    #     Check if a user can view a specific song.
    #     Logic:
    #     1. User must be logged in
    #     2. User must be a member of the org that owns the song
    #     3. User's role must be ADMIN or MEMBER
    #     Args:
    #         user: The CustomUser trying to view the song
    #         song: The Song object being accessed
    #     Returns:
    #         True if user can view, False otherwise
    #     """
    #     # 1. is user logged in
    #     if not user.is_authenticated:
    #         return False
    #
    #     # 2. We need to find the Organization that has this auth account
    #     try:
    #         owning_organization = Organization.objects.get(user=song.user)
    #     except Organization.DoesNotExist:
    #         # Edge case: song.user is not an organization account
    #         return song.user == user
    #
    #     # 3. Check if the viewing user is a member of that org
    #     # This uses  existing get_role() method from Organization model
    #     user_role = owning_organization.get_role(user)
    #
    #     # If user has no role in this org, they can't see the song
    #     if user_role is None:
    #         return False
    #
    #     # 4. Check if the role allows song viewing
    #     #  ADMIN and MEMBER can view songs
    #     allowed_role_ids = [Role.ADMIN, Role.MEMBER]
    #
    #     return user_role.id in allowed_role_ids
    #
    # @staticmethod
    # def can_manage_song(user, organization):
    #     """Check if user can add, edit or delete songs to this organization."""
    #     if not user.is_authenticated:
    #         return False
    #
    #     user_role = organization.get_role(user)
    #
    #     if user_role is None:
    #         return False
    #
    #     # Only ADMIN can manage songs
    #     return user_role.id == Role.ADMIN
    #
    # @staticmethod
    # def get_song_organization(song):
    #     """
    #     Helper method: Find which organization owns a song.
    #     This is useful when you need to know the org but not check permissions.
    #     Args:
    #         song: The Song object
    #     Returns:
    #         Organization object or None if not found
    #     """
    #     try:
    #         return Organization.objects.get(user=song.user)
    #     except Organization.DoesNotExist:
    #         return None
    #
    # # MEMBER LIST ACCESS METHODS
    # @staticmethod
    # def get_visible_members(user, organization):
    #     """
    #     Return a queryset of Person objects that the user can see in this organization.
    #     This returns a Django QuerySet, not True/False!
    #     Args:
    #         user: The individual CustomUser (from request.user)
    #         organization: The Organization we're viewing members of
    #     Returns:
    #         QuerySet of Person objects (can be empty)
    #     LOGIC:
    #     - ADMIN: sees ALL members (all roles)
    #     - MEMBER: sees only ADMIN and MEMBER roles (no SUPPORTER/EXTERNAL)
    #     - SUPPORTER/EXTERNAL/Anonymous: sees NOTHING (empty queryset)
    #     """
    #     # 1. is user logged in
    #     if not user.is_authenticated:
    #         return Person.objects.none()  # Empty queryset
    #
    #     # 2. Get user's role in this organization
    #     user_role = organization.get_role(user)
    #
    #     # 3. If no role, return empty queryset
    #     if user_role is None:
    #         return Person.objects.none()
    #
    #     # 4. Filter based on role   # This is where magic happens
    #     # ADMIN sees everyone
    #     if user_role.id == Role.ADMIN:
    #         return Person.objects.filter(
    #             memberships__organization=organization
    #         ).distinct()
    #     # MEMBER sees only ADMIN and MEMBER roles
    #     elif user_role.id == Role.MEMBER:
    #         return Person.objects.filter(
    #             memberships__organization=organization,
    #             memberships__role__id__in=[Role.ADMIN, Role.MEMBER]
    #         ).distinct()
    #     # SUPPORTER, EXTERNAL, or any other role: see nothing
    #     else:
    #         return Person.objects.none()
