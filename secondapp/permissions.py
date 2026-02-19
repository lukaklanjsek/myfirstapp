# permissions.py

from django.core.exceptions import PermissionDenied
from .models import Organization, Role, Person


class AccessControl:
    """
    Centralized access control for the application.
    All permission checks go through this class.
    """

    # SONG ACCESS METHODS
    @staticmethod
    def can_view_song(user, song):
        """
        Check if a user can view a specific song.
        Logic:
        1. User must be logged in
        2. User must be a member of the org that owns the song
        3. User's role must be ADMIN or MEMBER
        Args:
            user: The CustomUser trying to view the song
            song: The Song object being accessed
        Returns:
            True if user can view, False otherwise
        """
        # 1. is user logged in
        if not user.is_authenticated:
            return False

        # 2. We need to find the Organization that has this auth account
        try:
            owning_organization = Organization.objects.get(user=song.user)
        except Organization.DoesNotExist:
            # Edge case: song.user is not an organization account
            return song.user == user

        # 3. Check if the viewing user is a member of that org
        # This uses  existing get_role() method from Organization model
        user_role = owning_organization.get_role(user)

        # If user has no role in this org, they can't see the song
        if user_role is None:
            return False

        # 4. Check if the role allows song viewing
        #  ADMIN and MEMBER can view songs
        allowed_role_ids = [Role.ADMIN, Role.MEMBER]

        return user_role.id in allowed_role_ids

    @staticmethod
    def get_song_organization(song):
        """
        Helper method: Find which organization owns a song.
        This is useful when you need to know the org but not check permissions.
        Args:
            song: The Song object
        Returns:
            Organization object or None if not found
        """
        try:
            return Organization.objects.get(user=song.user)
        except Organization.DoesNotExist:
            return None

    # MEMBER LIST ACCESS METHODS
    @staticmethod
    def get_visible_members(user, organization):
        """
        Return a queryset of Person objects that the user can see in this organization.
        This returns a Django QuerySet, not True/False!
        Args:
            user: The individual CustomUser (from request.user)
            organization: The Organization we're viewing members of
        Returns:
            QuerySet of Person objects (can be empty)
        LOGIC:
        - ADMIN: sees ALL members (all roles)
        - MEMBER: sees only ADMIN and MEMBER roles (no SUPPORTER/EXTERNAL)
        - SUPPORTER/EXTERNAL/Anonymous: sees NOTHING (empty queryset)
        """
        # 1. is user logged in
        if not user.is_authenticated:
            return Person.objects.none()  # Empty queryset

        # 2. Get user's role in this organization
        user_role = organization.get_role(user)

        # 3. If no role, return empty queryset
        if user_role is None:
            return Person.objects.none()

        # 4. Filter based on role   # This is where magic happens
        # ADMIN sees everyone
        if user_role.id == Role.ADMIN:
            return Person.objects.filter(
                memberships__organization=organization
            ).distinct()
        # MEMBER sees only ADMIN and MEMBER roles
        elif user_role.id == Role.MEMBER:
            return Person.objects.filter(
                memberships__organization=organization,
                memberships__role__id__in=[Role.ADMIN, Role.MEMBER]
            ).distinct()
        # SUPPORTER, EXTERNAL, or any other role: see nothing
        else:
            return Person.objects.none()


    @staticmethod
    def get_visible_members(user, organization):
        from .models import Person

        print(f"DEBUG 1: user = {user}")
        print(f"DEBUG 2: user.is_authenticated = {user.is_authenticated}")

        if not user.is_authenticated:
            print("DEBUG 3: User not authenticated, returning none")
            return Person.objects.none()

        user_role = organization.get_role(user)
        print(f"DEBUG 4: user_role = {user_role}")
        print(f"DEBUG 5: user_role.id = {user_role.id if user_role else 'None'}")

        if user_role is None:
            print("DEBUG 6: No role, returning none")
            return Person.objects.none()

        # ADMIN sees everyone
        if user_role.id == Role.ADMIN:
            print("DEBUG 7: User is ADMIN, showing all members")
            queryset = Person.objects.filter(
                memberships__organization=organization
            ).distinct()
            print(f"DEBUG 8: Queryset count = {queryset.count()}")
            return queryset

        # MEMBER sees only ADMIN and MEMBER roles
        elif user_role.id == Role.MEMBER:
            print("DEBUG 9: User is MEMBER, showing ADMIN+MEMBER only")
            queryset = Person.objects.filter(
                memberships__organization=organization,
                memberships__role__id__in=[Role.ADMIN, Role.MEMBER]
            ).distinct()
            print(f"DEBUG 10: Queryset count = {queryset.count()}")
            return queryset

        # SUPPORTER, EXTERNAL: see nothing
        else:
            print(f"DEBUG 11: User is {user_role.title}, returning none")
            return Person.objects.none()

