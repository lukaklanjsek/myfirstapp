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

    # BASIC HELPERS -------------------------------------------------------------------

    @classmethod
    def get_auth_person(cls, auth_user):
        """
        Get the viewer's personal Person profile.
        This Person is directly linked to their auth account (and not to the org).
        Args: auth_user: the authenticated CustomUser
        Returns: Person object or None
        """
        if not auth_user.is_authenticated:
            return None

        return Person.objects.filter(
            user=auth_user,
            owner__isnull=True
        ).first()  # Returns None if not found


    @classmethod
    def get_username(cls, url_username):
        """Get CustomUser from URL."""

        try:
            return CustomUser.objects.get(username=url_username)
        except CustomUser.DoesNotExist:
            return None

    #   ----------------------------------------------------------

    @classmethod
    def get_org_roles(cls, user, url_username):
        """
        Get viewer's role in an organization- url_username.
        Args:
            auth_user = viewer's CustomUser
            url_username = object's
        Returns:
            all roles of viewer inside an organization
        """
        if not user.is_authenticated:
            return Role.objects.none()

        viewer_person = cls.get_auth_person(user)
        if not viewer_person:
            return Role.objects.none()

        membership = Membership.objects.filter(
            user__username=url_username,
            person__owner=viewer_person
        ).select_related('person').first()

        return membership.person.roles.all() if membership else Role.objects.none()

 #
 #
 #






    @classmethod
    def _user_memberships(cls, auth_user):
        """
        Get all memberships where auth_user is involved.
        This includes:
        - Direct memberships (auth_user is the user)
        - Org memberships (auth_user owns a person in an org)
        """
        if not auth_user.is_authenticated:
            return Membership.objects.none()

        # Get the personal profile (owner=NULL)
        personal_profile = cls.get_auth_person(auth_user)
        if not personal_profile:
            return Membership.objects.none()

        # Find memberships where the person is owned by this personal profile
        return Membership.objects.filter(
            person__owner=personal_profile
        ).select_related("user", "person")


    # @classmethod
    # def get_user_role_in_org(cls, auth_user, url_username):
    #     """Get user's role in a specific membership."""
    #     try:
    #         user_url = CustomUser.objects.get(username=url_username)
    #     except CustomUser.DoesNotExist:
    #         return None
    #
    #     membership = cls._user_memberships(auth_user).filter(
    #         user=user_url  # Memberships hanging on the URL user
    #     ).first()
    #
    #     return membership.person.roles.all() if membership else None


    # @classmethod
    # def filter_queryset_by_org(cls, auth_user, queryset):
    #     """
    #     Filter a queryset to only include items from organizations the user has access to.
    #     Args:
    #         auth_user: CustomUser instance
    #         queryset: QuerySet with an 'organization_id' field
    #     Returns: Filtered QuerySet containing only items from user's organizations
    #     """
    #     org_user_ids = cls._user_memberships(auth_user).values_list('user_id', flat=True)
    #
    #     return queryset.filter(
    #         user_id__in=org_user_ids
    #     ).distinct()

    @classmethod
    def has_permission(cls, auth_user, action, url_username):
        """
            Check if a user has permission to perform an action.
            Args:
                auth_user: CustomUser instance (the viewer)
                action: String action name (e.g., 'view', 'create', 'update', 'delete')
                url_username: Username from URL (the context)
            Returns:
                Boolean indicating whether user has the specified permission
            """
        try:
            target_user = CustomUser.objects.get(username=url_username)
        except CustomUser.DoesNotExist:
            return False

        roles = cls.get_org_roles(auth_user, url_username)
        if not roles.exists():
            return False

        # Check if ANY of the user's roles grants the permission
        for role in roles:
            role_permissions = cls.ROLE_PERMISSIONS.get(role.id, set())
            if action in role_permissions:
                return True

        return False

    @classmethod
    def get_viewable_people_queryset(cls, auth_user):
        """
        Get all Person objects from organizations where the user is a member.
        Args:  auth_user: CustomUser instance
        Returns: QuerySet of Person objects from user's organizations
        Note: Returns people who are linked to users that are members of the same organizations
        """
        if not auth_user.is_authenticated:
            return Person.objects.none()

        # Get all Person profiles from orgs where auth_user is a member
        org_user_ids = cls._user_memberships(auth_user).values_list("user_id", flat=True)

        return Person.objects.filter(
            memberships__user_id__in=org_user_ids,  # Person is in these orgs
            owner__isnull=False  # Exclude personal profiles
        ).distinct()

    # @classmethod
    # def can_access(cls, auth_user, action, url_username, queryset=None):
    #     """
    #     Check permission and filter queryset if provided.
    #     Args:
    #         auth_user: The viewer
    #         action: Permission type
    #         url_username: Username from URL
    #         queryset: Optional queryset to filter
    #     """
    #     if not cls.has_permission(auth_user, action, url_username):
    #         return False, queryset.none() if queryset is not None else None
    #
    #     if queryset is not None:
    #         return True, cls.filter_queryset_by_org(auth_user, queryset)
    #     return True, None

    @classmethod
    def filter_person_details(cls, auth_user, person, url_username):
        """
        Filter person details based on the viewer's role.
        Args:
            auth_user: The viewer
            person: Person object being viewed
            url_username: Username from URL (the context)
        Returns:
            Dictionary with allowed fields or None
        """
        target_user = cls.get_username(url_username)
        if not target_user:
            return None

        membership = cls._user_memberships(auth_user).filter(
            user=target_user
        ).select_related("person").first()

        if not membership:
            return None

        # Check if the person being viewed is in the same context
        person_in_context = Membership.objects.filter(
            user=target_user,
            person=person
        ).exists()

        if not person_in_context:
            return None

        # Get viewer's roles
        viewer_roles = membership.person.roles.values_list('id', flat=True)

        base_data = {
            "first_name": person.first_name,
            "last_name": person.last_name,
            "skills": person.skills.values_list("title", flat=True),
        }

        if Role.ADMIN in viewer_roles:
            return {
                **base_data,
                "email": person.email,
                "phone": person.phone,
                "address": person.address,
                "birth_date": person.birth_date,
                "created_at": person.created_at,
                "updated_at": person.updated_at,
            }

        if Role.MEMBER in viewer_roles:
            return base_data

        return None

    @classmethod
    def get_visible_members(cls, auth_user, url_username):
        """
        Get memberships visible to a user within an organization.
        Args:
            auth_user: CustomUser viewing the member list
            organization: Organization to get members from
        Returns: QuerySet of Membership objects the user can see
        Visibility rules:
            - ADMIN: Can see all members
            - MEMBER: Can see only ADMIN and MEMBER roles
            - SUPPORTER: Can see only ADMIN roles
            - EXTERNAL: Cannot see any members
        """
        url_user = cls.get_username(url_username)
        viewer_roles = cls.get_org_roles(auth_user, url_username)

        if auth_user != url_user:
            # Get the target user from username
            if not url_user:
                return Membership.objects.none()


            if not viewer_roles or not viewer_roles.exists():
                return Membership.objects.none()

        # Get memberships for this url user
        memberships = Membership.objects.filter(
            user=url_user
        ).select_related("person").prefetch_related("person__roles")

        if not viewer_roles:
            return Membership.objects.none()

        viewer_role_ids = set(viewer_roles.values_list('id', flat=True))

        # admin sees everyone
        if Role.ADMIN in  viewer_role_ids:
            return memberships

        # member sees members and admins
        if Role.MEMBER in viewer_role_ids:
            return memberships.filter(person__roles__id__in=[Role.ADMIN, Role.MEMBER])


        if Role.SUPPORTER in viewer_role_ids:
            return memberships.filter(role_id=Role.ADMIN)

        return Membership.objects.none()

    @classmethod
    def can_view_song(cls, auth_user, song):
        """
        Admin + Member can view songs
        Supporter/External do not
        Include both organizational or individual song owners.
        """
        if not auth_user.is_authenticated:
            return False

        owner_user = song.user

        # Check if song belongs to an organization
        org = Organization.objects.filter(user=owner_user).first()
        if org:
            memberships = cls._user_memberships(auth_user).filter(
                user=org.user,
                person__roles__id__in=[Role.ADMIN, Role.MEMBER]
            )
            return memberships.exists()

        # Personal song - only owner can view
        return owner_user == auth_user

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
            user=owner_user,
            person__roles__id__in=[Role.ADMIN, Role.MEMBER]
        )
        if not memberships.exists():
            return Song.objects.none()

        return Song.objects.filter(user=org.user)

    @classmethod
    def can_manage_song(cls, auth_user, song):
        """
        Returns True if auth_user can create/update/delete the given song.
        Rules:
        - Personal songs: owner must be auth_user
        - Org songs: auth_user must be ADMIN in the org
        """
        if not auth_user.is_authenticated:
            return False

        owner_user = song.user

        # Check if owner_user represents an organization
        org = Organization.objects.filter(user=owner_user).first()

        if not org:
            # Personal songs - only owner can manage
            return auth_user == owner_user

        # Organizational songs - must be ADMIN
        roles = cls.get_org_roles(auth_user, org.user.username)
        return roles.filter(id=Role.ADMIN).exists()