# utils.py

class SongQueryHelper:
    @staticmethod
    def get_personal_songs(user):
        return Song.objects.filter(user = user, user__is_service_account=False)

    @staticmethod
    def get_organization_songs(organization):
        return Song.objects.filter(user = organization.service_account)

    @staticmethod
    def get_user_accessible_songs(user):
        personal = Song.objects.filter(user=user)

        person = user.persons.first()
        if not person:
            return personal

        owned_persons = person.owned_persons.all()
        memberships = Membership.objects.filter(
            person in owned_persons,
            is_active = True
        ).select_related("organization__service_account")

        org_service_accounts = [m.organization.service_account for m in memberships]
        org_songs = Song.objects.filter(user__in=org_service_accounts)

        return personal | org_songs