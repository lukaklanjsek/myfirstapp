# utils.py
from .models import (Song, Membership, CustomUser,
                     Person, PersonRole, PersonSkill,
                     MembershipPeriod, Role, Skill,
                     Singer)
import csv, datetime
from django.contrib import messages
from .permissions import AccessControl
from django.db import transaction
from django.http import HttpResponseForbidden

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

ALLOWED_SONG_KEYS = [
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

def import_songs(org_user, request, file_path, delimiter=";"):
    """
    Import songs from a CSV file into the database for a given organization user.


    Potential issues identified:
    - Line 54: Membership filter syntax error: "person in owned_persons" should use __in
    - Empty string checks: Some fields may need better None handling
    - No validation for duplicate songs (same title/composer combination)
    - No transaction rollback if bulk import partially fails
    - PersonSkill.COMPOSER and Skill.COMPOSER naming inconsistency needs verification
    """
    viewer_user = request.user
    imported_count = 0

    # Check if viewer can manage this org_user
    if request.user != org_user:
        has_permission = AccessControl.can_edit_event(
            request.user, org_user
        ).exists()

        if not has_permission:
            messages.error(request, "You don't have permission to import.")

    with open(file_path, 'r') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        headers = reader.fieldnames
        messages.info(request, f"headers: {headers}")

        for h in headers:
            if h not in ALLOWED_SONG_KEYS:
                return None
        today = datetime.date.today()

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
                    memberships__user=org_user,
                    person_skill__skill_id = Skill.COMPOSER
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
                    PersonSkill.objects.create(person=composer, skill_id=Skill.COMPOSER)

                existing_poet = Person.objects.filter(
                    last_name=poet_last_name,
                    first_name=poet_first_name,
                    memberships__user=org_user,
                    person_skill__skill_id = Skill.POET
                ).first()

                if existing_poet:
                    poet = existing_poet
                else:    # Create new composer if not found in organization's membership
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
                    PersonSkill.objects.create(person=poet, skill_id=Skill.POET)

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
                imported_count += 1
            except Exception as e:
                message_text = f"Error importing row {reader.line_num}: {str(e)}"
                messages.error(request, message_text)
                continue  # Continue to next row on error

        return {
            'success': True,
            'count': imported_count
        }


FIRST_NAME_KEY = "first_name"
LAST_NAME_KEY = "last_name"
EMAIL_KEY = "email"
ADDRESS_KEY = "address"
BIRTH_DATE_KEY = "birth_date"
LANDLINE_PHONE_KEY = "landline_phone"
MOBILE_PHONE_KEY = "mobile_phone"
VOICE_KEY = "voice"
ACTIVITY_KEY = "activity"

ALLOWED_PERSON_KEYS = [
    FIRST_NAME_KEY,
    LAST_NAME_KEY,
    EMAIL_KEY,
    ADDRESS_KEY,
    BIRTH_DATE_KEY,
    LANDLINE_PHONE_KEY,
    MOBILE_PHONE_KEY,
    VOICE_KEY,
    ACTIVITY_KEY,
]

VOICE_TYPES = {
    'Soprano': {"Soprano", "SOPRANO", "soprano", "Sopran", "SOPRAN", "sopran", "Sop", "SOP", "sop", "S", "s"},
    'Alto': {"Alto", "ALTO", "alto", "Alt", "ALT", "alt", "A", "a", "Contralto", "CONTRALTO", "contralto"},
    'Tenor': {"Tenor", "TENOR", "tenor", "Ten", "TEN", "ten", "T", "t"},
    'Bass': {"Bass", "BASS", "bass", "Basso", "BASSO", "basso", "Bas", "BAS", "bas", "B", "b"}
}

# Reverse mapping for O(1) lookup
VOICE_LOOKUP = {variant: voice for voice, variants in VOICE_TYPES.items() for variant in variants}

# ALLOWED_HEADERS = ['first_name', 'last_name', 'email', 'address', 'birth_date',
#                    'landline_phone', 'mobile_phone', 'voice', 'activity']


def import_persons(org_user, request, file_path, delimiter=";"):
    """Import persons from CSV file."""
    imported_count = 0
    skipped_count = 0
    error_details = []

    # Check permissions
    if request.user != org_user:
        has_permission = AccessControl.can_edit_event(request.user, org_user).exists()
        if not has_permission:
            messages.error(request, "You don't have permission to import.")
            return {'success': False, 'count': 0, 'error': 'Permission denied'}

    # Helper: parse date from multiple formats
    def parse_date(date_str):
        if not date_str:
            return None
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d.%m.%Y']:
            try:
                return datetime.datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None

    # Helper: parse activity date ranges
    def parse_activity(activity_str):
        if not activity_str:
            return []

        ranges = []
        for date_range in activity_str.split(','):
            parts = date_range.strip().replace(' ', '').split('-')

            if len(parts) == 3:  # Ongoing: YYYY-MM-DD
                start = parse_date(f"{parts[0]}-{parts[1]}-{parts[2]}")
                if start:
                    ranges.append({'start': start, 'end': None})
            elif len(parts) == 6:  # Completed: YYYY-MM-DD-YYYY-MM-DD
                start = parse_date(f"{parts[0]}-{parts[1]}-{parts[2]}")
                end = parse_date(f"{parts[3]}-{parts[4]}-{parts[5]}")
                if start and end:
                    ranges.append({'start': start, 'end': end})

        return ranges

    # Process CSV
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=delimiter)

        for row in reader:
            try:
                # Extract and clean data
                first_name = row.get(FIRST_NAME_KEY, '').strip()
                last_name = row.get(LAST_NAME_KEY, '').strip()
                email = row.get(EMAIL_KEY, '').strip() or None
                address = row.get(ADDRESS_KEY, '').strip() or None
                birth_date = parse_date(row.get(BIRTH_DATE_KEY, '').strip())
                phone = row.get(MOBILE_PHONE_KEY, '').strip() or row.get(LANDLINE_PHONE_KEY, '').strip() or None
                voice = row.get(VOICE_KEY, '').strip()
                activity_ranges = parse_activity(row.get(ACTIVITY_KEY, '').strip())

                # Validate required fields
                if not first_name or not last_name:
                    error_details.append(f"Row {reader.line_num}: Missing name")
                    skipped_count += 1
                    continue

                with transaction.atomic():
                    # Check if person already exists
                    if Person.objects.filter(
                            last_name=last_name,
                            first_name=first_name,
                            memberships__user=org_user
                    ).exists():
                        skipped_count += 1
                        continue

                    # Create person
                    person = Person.objects.create(
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        address=address,
                        birth_date=birth_date,
                        phone=phone,
                        user=None,
                        owner=None
                    )

                    # Assign voice and skill
                    voice_type = VOICE_LOOKUP.get(voice)
                    if voice_type:
                        Singer.objects.create(person=person, voice=voice_type)
                        PersonSkill.objects.create(person=person, skill_id=Skill.SINGER)
                    else:
                        if voice:
                            error_details.append(f"Row {reader.line_num}: Unknown voice '{voice}', assigned Conductor")
                        PersonSkill.objects.create(person=person, skill_id=Skill.CONDUCTOR)

                    # Process membership periods
                    has_active = any(period['end'] is None for period in activity_ranges)

                    #  Only create Membership when has_active=True
                    if has_active:
                        Membership.objects.create(user=org_user, person=person)

                    for period in activity_ranges:
                        MembershipPeriod.objects.create(
                            user=org_user,
                            person=person,
                            role_id=Role.MEMBER,
                            started_at=period['start'],
                            ended_at=period['end']
                        )

                    # Assign role
                    PersonRole.objects.create(
                        person=person,
                        role_id=Role.MEMBER if has_active else Role.EXTERNAL
                    )

                    imported_count += 1

            except Exception as e:
                error_details.append(f"Row {reader.line_num}: {str(e)}")
                continue

    messages.success(request, f"Import complete: {imported_count} imported, {skipped_count} skipped")

    return {
        'success': True,
        'count': imported_count,
        'skipped': skipped_count,
        'errors': len(error_details),
        'error_details': error_details
    }


def import_events(self, org_user, request, file_path, delimiter=";"):
    url_username = self.kwargs.get("username")
    pass


