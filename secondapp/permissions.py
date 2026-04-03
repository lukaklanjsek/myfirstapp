# permissions.py

from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.template.context_processors import request

from .models import Organization, Role, Person, CustomUser, Membership, Song, PersonRole


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

        return Person.objects.get(
            user=auth_user,
            owner__isnull=True
        )  # Raises exteption if not found


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
        Get viewer's role in an organization.

        Two cases:
        1. User viewing their own memberships -> return ADMIN role
        2. User's person owns a person with membership in this org -> return that person's roles

        Args:
            user: Viewer's CustomUser
            url_username: Organization username being viewed

        Returns:
            QuerySet of Role objects
        """
        # print(f"=== get_org_roles ===")
        # print(f"user: {user.username}")
        # print(f"url_username: {url_username}")
        # print(f"url_username type: {type(url_username)}")

        if not user.is_authenticated:
            print("User not authenticated")
            return Role.objects.none()

        # Case 1: User viewing their own memberships
        if user.username == url_username:
            # print("user username is url_username returning role:", )
            return Role.objects.filter(id=Role.ADMIN)

        # Case 2: User's person owns a person with membership in this org
        auth_person = cls.get_auth_person(user)
        if not auth_person:
            return Role.objects.none()

        # Find a person owned by auth_person that has a membership in the target org
        membership = Membership.objects.filter(
            user__username=url_username,
            person__owner=auth_person
        ).select_related('person').first()

        if not membership:
            return Role.objects.none()

        return membership.person.roles.all()
#
#         org_username = url_username
#
#         auth_person = cls.get_auth_person(user)
#         print(f"viewer_person: {auth_person}")
#
#         if not auth_person:
#             print("No viewer person found")
#             return Role.objects.none()
# ####################################################
#         org_person = Person.objects.filter(
#             memberships__user__username=org_username,  # Has membership in this org
#             owner=auth_person  # Owned by the viewer
#         ).first()
#         print(f"org_person (owned by viewer): {org_person}")
#         if not org_person:  # Allow editing and viewing ones own memberships
#             print(f"Using auth_person directly: {org_person}")
#             own_membership = Membership.objects.filter(
#                 user__username=org_username,
#                 person=auth_person
#             ).exists()
#
#             if own_membership:
#                 org_person = auth_person
#                 print(f"Using auth_person directly: {org_person}")
#
#         if not org_person:
#             print("No org person found for viewer")
#             return Role.objects.none()
#         # Get roles via PersonRole
#         person_roles = PersonRole.objects.filter(
#             person=org_person
#         ).select_related('role')
#
#         print(f"PersonRole entries: {person_roles.count()}")
#         for pr in person_roles:
#             print(f"  - {pr.person} has role {pr.role}")
#
#         # Extract Role objects
#         role_ids = person_roles.values_list('role_id', flat=True)
#         roles = Role.objects.filter(id__in=role_ids)
#
#         print(f"Final roles: {list(roles.values_list('title', flat=True))}")
#
# ###########################################333
#         membership = Membership.objects.filter(
#             user__username=url_username,
#             person__owner=auth_person
#         ).select_related('person').first()
#         print(f"membership found: {membership}")
#         #################################################
#         all_memberships = Membership.objects.filter(
#             user__username=org_username
#         ).select_related('person')
#
#         print(f"All memberships for {org_username}:")
#         for m in all_memberships:
#             print(f"  Person: {m.person}, Owner: {m.person.owner}, Owner type: {type(m.person.owner)}")
#         print(f"Looking for person.owner = {auth_person} (type: {type(auth_person)})")
#
#         print(f"membership found: {membership}")
#         ###############################################
#
#         # return membership.person.roles.all() if membership else Role.objects.none()
#         if membership:
#             roles = membership.person.roles.all()
#             print(f"Membership roles: {list(roles.values_list('id', 'title'))}")
#             return roles
#         else:
#             print("returning 'roles'", roles)
#             return roles






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

    @classmethod
    def get_member_person(cls, auth_user, org_user):
        """
        Return auth_user's Person record within org_user's organization, or None.
        Reuses _user_memberships to follow the same ownership chain used elsewhere.
        """
        if not auth_user.is_authenticated:
            return None
        membership = cls._user_memberships(auth_user).filter(
            user=org_user
        ).select_related('person').first()
        return membership.person if membership else None


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
            auth_user = CustomUser.objects.get(username=url_username)
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
    def can_view_member_list(cls, auth_user, url_username):
        """
        Return queryset of Memberships that auth_user can view:
        - Personal memberships if owner_user is same as auth_user
        - Or org memberships if auth_user is ADMIN or MEMBER of that org
        """
        if not auth_user.is_authenticated:
            return Membership.objects.none()

        # personal memberships
        if url_username == auth_user:
            return Membership.objects.filter(user=auth_user)

        # org memberships - check if auth_user has proper role
        memberships = cls._user_memberships(auth_user).filter(
            user=url_username,  # Memberships under owner_user's "org"
            person__roles__id__in=[Role.ADMIN, Role.MEMBER]
        )
        if not memberships.exists():
            return Membership.objects.none()

        return Membership.objects.filter(user=url_username)


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
        # print(f"=== DEBUG get_visible_members ===")
        # print(f"auth_user: {auth_user.username}")
        # print(f"url_username (input): {url_username}")
        # print(f"url_username type: {type(url_username)}")

        # Normalize url_username to a string
        if isinstance(url_username, CustomUser):
            org_username_str = url_username.username
            url_user = url_username
        else:
            org_username_str = url_username
            try:
                url_user = CustomUser.objects.get(username=url_username)
            except CustomUser.DoesNotExist:
                print("No url_user found - returning empty queryset")
                return Membership.objects.none()

        # print(f"url_user object: {url_user}")
        # print(f"org_username_str: {org_username_str}")

        # Get memberships for this organization
        memberships = Membership.objects.filter(
            user=url_user
        ).select_related("person").prefetch_related("person__roles")

        # print(f"Total memberships for {org_username_str}: {memberships.count()}")
        # for m in memberships:
        #     print(f"  - Member: {m.person}, Roles: {list(m.person.roles.values_list('id', flat=True))}")

        # PASS THE STRING to get_org_roles
        viewer_roles = cls.get_org_roles(auth_user, org_username_str)
        # print(f"Viewer roles: {list(viewer_roles.values_list('id', flat=True))}")

        if not viewer_roles.exists():
            print("Viewer has no roles - returning empty queryset")
            return Membership.objects.none()

        viewer_role_ids = set(viewer_roles.values_list('id', flat=True))
        # print(f"Viewer role IDs: {viewer_role_ids}")

        # ADMIN sees everyone
        if Role.ADMIN in viewer_role_ids:
            # print("Viewer is ADMIN - returning all memberships")
            return memberships

        # MEMBER sees ADMIN and MEMBER roles only
        if Role.MEMBER in viewer_role_ids:
            filtered = memberships.filter(
                person__roles__id__in=[Role.ADMIN, Role.MEMBER]
            ).distinct()
            # print(f"Viewer is MEMBER - returning {filtered.count()} filtered memberships")
            return filtered

        # SUPPORTER sees ADMIN roles only
        if Role.SUPPORTER in viewer_role_ids:
            filtered = memberships.filter(
                person__roles__id=Role.ADMIN
            ).distinct()
            # print(f"Viewer is SUPPORTER - returning {filtered.count()} filtered memberships")
            return filtered

        print("No matching role - returning empty queryset")
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

    @classmethod
    def can_add_event(cls, auth_user, url_username):
        """
        Return queryset of Memberships that auth_user can view:
        - Personal memberships if owner_user is same as auth_user
        - Or org memberships if auth_user is ADMIN or MEMBER of that org
        """
        if not auth_user.is_authenticated:
            return Membership.objects.none()

        # personal memberships
        if url_username == auth_user:
            return Membership.objects.filter(user=auth_user)

        # org memberships - check if auth_user has proper role
        memberships = cls._user_memberships(auth_user).filter(
            user=url_username,  # Memberships under owner_user's "org"
            person__roles__id__in=[Role.ADMIN] #, Role.MEMBER
        )
        if not memberships.exists():
            return Membership.objects.none()

        return Membership.objects.filter(user=url_username)

    @classmethod
    def can_edit_event(cls, auth_user, url_username):
        """
        Return queryset of Memberships that auth_user can view:
        - Personal memberships if owner_user is same as auth_user
        - Or org memberships if auth_user is ADMIN or MEMBER of that org
        """
        if not auth_user.is_authenticated:
            return Membership.objects.none()

        # personal memberships
        if url_username == auth_user:
            return Membership.objects.filter(user=auth_user)

        # org memberships - check if auth_user has proper role
        memberships = cls._user_memberships(auth_user).filter(
            user=url_username,  # Memberships under owner_user's "org"
            person__roles__id__in=[Role.ADMIN, Role.MEMBER]
        )
        if not memberships.exists():
            return Membership.objects.none()

        return Membership.objects.filter(user=url_username)