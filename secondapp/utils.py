# utils.py
from .models import Song, Membership, CustomUser, Person, PersonRole, PersonSkill, MembershipPeriod, Role, Skill
import csv, datetime
from django.contrib import messages

class SongQueryHelper:
    @staticmethod
    def get_personal_songs(user):
        return Song.objects.filter(user = user)

    @staticmethod
    def get_organization_songs(organization):
        return Song.objects.filter(user = organization.user)

    @staticmethod
    def get_user_accessible_songs(user):
        personal = Song.objects.filter(user=user)

        person = user.persons.first()
        if not person:
            return personal

        owned_persons = person.owned_persons.all()
        memberships = Membership.objects.filter(
            person in owned_persons,
            # is_active = True
        ).select_related("organization__user")

        org_user = [m.organization.user for m in memberships]
        org_songs = Song.objects.filter(user__in=org_user)

        return personal | org_songs



INTERNAL_ID_KEY = "internal_id"
TITLE_KEY = "title"
COMPOSER_LAST_NAME_KEY = "composer_last_name"
COMPOSER_FIRST_NAME_KEY = "composer_first_name"
POET_LAST_NAME_KEY = "poet_last_name"
POET_FIRST_NAME_KEY = "poet_first_name"
YEAR_KEY = "year"
GROUP_KEY = "group"
NUMBER_OF_PAGES_KEY = "number_of_pages"
NUMBER_OF_COPIES_KEY = "number_of_copies"
NUMBER_OF_VOICES_KEY = "number_of_voices"
ADDITIONAL_NOTES_KEY = "additional_notes"
LYRICS_KEY = "lyrics"

ALLOWED_KEYS = [
    INTERNAL_ID_KEY,
    TITLE_KEY,
    COMPOSER_LAST_NAME_KEY,
    COMPOSER_FIRST_NAME_KEY,
    POET_LAST_NAME_KEY,
    POET_FIRST_NAME_KEY,
    YEAR_KEY,
    GROUP_KEY,
    NUMBER_OF_PAGES_KEY,
    NUMBER_OF_COPIES_KEY,
    NUMBER_OF_VOICES_KEY,
    ADDITIONAL_NOTES_KEY,
    LYRICS_KEY,
]

def import_data(self, file_path, delimiter=";"):
    url_username = self.kwargs.get("username")
    # viewer_user = self.request.user

    with open(file_path, 'r') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        headers = reader.fieldnames
        messages.info(self.request, f"headers: {headers}")

        for h in headers:
            if h not in ALLOWED_KEYS:
                return None
        today = datetime.date.today()
        org_user = CustomUser.objects.get(username=url_username)

        for row in reader:
            # Split the row data according to headers
            internal_id_value = row.get(INTERNAL_ID_KEY, '').strip()
            title_value = row.get(TITLE_KEY, '').strip()
            composer_last_name = row.get(COMPOSER_LAST_NAME_KEY, '').strip()
            composer_first_name = row.get(COMPOSER_FIRST_NAME_KEY, '').strip()
            poet_last_name = row.get(POET_LAST_NAME_KEY, '').strip()
            poet_first_name = row.get(POET_FIRST_NAME_KEY, '').strip()
            year_value = row.get(YEAR_KEY, '').strip()
            group_value = row.get(GROUP_KEY, '').strip()
            number_of_pages_value = row.get(NUMBER_OF_PAGES_KEY, '').strip()
            number_of_copies_value = row.get(NUMBER_OF_COPIES_KEY, '').strip()
            number_of_voices_value = row.get(NUMBER_OF_VOICES_KEY, '').strip()
            additional_notes_value = row.get(ADDITIONAL_NOTES_KEY, '').strip()
            lyrics_value = row.get(LYRICS_KEY, '').strip()
            try:   # get organization username from url
                # Check if person exists in the organization's membership
                existing_composer = Person.objects.filter(   # does composer already exist in our membership?
                    last_name=composer_last_name,
                    first_name=composer_first_name,
                    memberships__user=org_user
                ).first()

                if existing_composer:
                    composer = existing_composer
                else:   # Create new composer if not found in organization's membership
                    composer = Person.objects.create(
                        last_name=composer_last_name,
                        first_name=composer_first_name,
                        user=None,
                        owner=None
                    )
                    Membership.objects.create(user=org_user, person=composer)
                    PersonRole.objects.create(person=composer, role_id=Role.EXTERNAL)
                    MembershipPeriod.objects.create(user=org_user, person=composer, role_id=Role.EXTERNAL,
                                                    started_at=today)
                    PersonSkill.objects.create(person=composer, role_id=Skill.COMPOSER)

                existing_poet = Person.objects.filter(
                    last_name=poet_last_name,
                    first_name=poet_first_name,
                    memberships__user=org_user
                ).first()
                if existing_poet:
                    poet = existing_poet
                else:
                    # Create new composer if not found in organization's membership
                    poet = Person.objects.create(
                        last_name=poet_last_name,
                        first_name=poet_first_name,
                        user=None,
                        owner=None
                    )
                    Membership.objects.create(user=org_user, person=poet)
                    PersonRole.objects.create(person=poet, role_id=Role.EXTERNAL)
                    MembershipPeriod.objects.create(user=org_user, person=poet, role_id=Role.EXTERNAL,
                                                    started_at=today)
                    PersonSkill.objects.create(person=poet, role_id=Skill.POET)
                # # Check if song already exists to avoid duplicates
                # existing_song = Song.objects.filter(
                #     title=title_value,
                #     composer=composer,
                #     poet=poet,
                #     user=org_user  # Also check user to ensure uniqueness per organization
                # ).first()
                #
                # if existing_song:
                #     continue  # Skip creating duplicate song

                Song.objects.create(   # Create new song with validated data
                    user=org_user,
                    internal_id=internal_id_value or None,  # Explicitly set None if empty
                    title=title_value,
                    composer=composer,
                    poet=poet,
                    number_of_pages=number_of_pages_value or None,
                    number_of_copies=number_of_copies_value or None,
                    number_of_voices=number_of_voices_value or None,
                    year=year_value or None,
                    group=group_value or None,
                    additional_notes=additional_notes_value or None,
                    lyrics=lyrics_value or None,
                    created_at=today,
                    updated_at=today,
                )
            except CustomUser.DoesNotExist:
                # Handle case where url_username doesn't exist
                return ValueError("your logged in user does not exist")
            except Exception as e:
                message_text = f"Error importing row {reader.line_num}: {str(e)}"
                messages.error(self.request, message_text)
            continue