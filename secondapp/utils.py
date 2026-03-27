# utils.py
from .models import (Song, Membership, CustomUser,
                     Person, PersonRole, PersonSkill,
                     MembershipPeriod, Role, Skill,
                     Singer, Voice, Event, Project)
import csv, datetime
from datetime import datetime, date
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
    """Import songs from a CSV file into the database for a given organization user."""
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
        today = date.today()

        for row in reader:
            # Split the row data according to headers
            internal_id_value = (row.get(INTERNAL_ID_KEY) or '').strip()
            title_value = (row.get(TITLE_KEY) or '').strip()
            composer_last_name = (row.get(COMPOSER_LAST_NAME_KEY) or '').strip()
            composer_first_name = (row.get(COMPOSER_FIRST_NAME_KEY) or '').strip()
            poet_last_name = (row.get(POET_LAST_NAME_KEY) or '').strip()
            poet_first_name = (row.get(POET_FIRST_NAME_KEY) or '').strip()
            year_value = (row.get(YEAR_KEY) or '').strip()
            group_value = (row.get(GROUP_KEY) or '').strip()
            number_of_pages_value = (row.get(NUMBER_OF_PAGES_KEY) or '').strip()
            number_of_copies_value = (row.get(NUMBER_OF_COPIES_KEY) or '').strip()
            number_of_voices_value = (row.get(NUMBER_OF_VOICES_KEY) or '').strip()
            additional_notes_value = (row.get(ADDITIONAL_NOTES_KEY) or '').strip()
            lyrics_value = (row.get(LYRICS_KEY) or '').strip()
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
    def parse_bday(date_str):
        if not date_str:
            return None
        for fmt in ['%Y-%m-%d']:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None

    # Helper: parse activity date ranges
    def parse_activity(activity_str):
        def parse_date(d):
            try:
                return datetime.strptime(d, '%Y-%m-%d').date()
            except ValueError:
                return None
        intervals = []
        for item in activity_str.split(','):
            item = item.strip()
            if not item:
                continue
            if item.endswith('-'):
                start = parse_date(item[:-1])
                if start:
                    intervals.append({'start': start, 'end': None})
            else:
                start = parse_date(item[0:10])
                end = parse_date(item[11:21])
                if start and end:
                    intervals.append({'start': start, 'end': end})
                else:
                    print("wrong date format:", item)
                # parts = item.split('-')
                # if len(parts) == 6:
                #     start = parse_date(f"{parts[0]}-{parts[1]}-{parts[2]}")
                #     end = parse_date(f"{parts[3]}-{parts[4]}-{parts[5]}")
                #     if start and end:
                #         intervals.append({'start': start, 'end': end})
                # else:
                #     print("wrong date format:", item)
        return intervals

    # Process CSV
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        headers = reader.fieldnames
        print(headers)

        for h in headers:
            if h not in ALLOWED_PERSON_KEYS:
                return None

        for row in reader:
            try:
                # Extract and clean data
                first_name = (row.get(FIRST_NAME_KEY) or '').strip()
                last_name = (row.get(LAST_NAME_KEY) or '').strip()
                email = (row.get(EMAIL_KEY) or '').strip() or None
                address = (row.get(ADDRESS_KEY) or '').strip() or None
                birth_date = parse_bday(row.get(BIRTH_DATE_KEY) or '')
                phone = (row.get(MOBILE_PHONE_KEY) or row.get(LANDLINE_PHONE_KEY) or '').strip() or None
                voice = (row.get(VOICE_KEY) or '').strip()
                activity_ranges = parse_activity(row.get(ACTIVITY_KEY) or '')

                person = Person.objects.create(     # Create person
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    address=address,
                    birth_date=birth_date,
                    phone=phone,
                    user=None,
                    owner=None
                )

                try:    # PersonSkill and Voice
                    voice_type = VOICE_LOOKUP.get(voice)
                    if voice_type:
                        PersonSkill.objects.create(person=person, skill_id=Skill.SINGER)
                        voice_instance = Voice.objects.get(name=voice_type)
                        Singer.objects.create(person=person, voice=voice_instance)
                        # print(f"Successfully assigned voice {voice_type} to {first_name}")
                    # else:
                        # PersonSkill.objects.create(person=person, skill_id=Skill.CONDUCTOR)
                        # print(f"Assigned skill conductor to {first_name}")
                except Exception as e:
                    # print(f"Warning: Failed to assign voice/skill to {first_name}: {str(e)}")
                    error_details.append(f"Row {reader.line_num} - Voice assignment failed for {first_name}: {str(e)}")

                has_active = bool(activity_ranges and any(period['end'] is None for period in activity_ranges))

                try: # Check if membership already exists to prevent duplicates
                    membership, created = Membership.objects.get_or_create(
                        user=org_user,
                        person=person
                    )
                    if created:
                        print(f"Created membership for {org_user} and {first_name}")
                    else:
                        print(f"Membership already exists for {org_user} and {first_name}")
                except Exception as e:
                    # print(f"Warning: Failed to create membership for {first_name}: {str(e)}")
                    error_details.append(f"Row {reader.line_num} - Membership failed for {first_name}: {str(e)}")

                # MembershipPeriod
                for period in activity_ranges:    # Process membership periods
                    try:
                        MembershipPeriod.objects.create(
                            user=org_user,
                            person=person,
                            role_id=Role.MEMBER,
                            started_at=period['start'],
                            ended_at=period['end']
                        )
                        print(f"added membership period to {first_name} {period['start']} - {period['end']}")
                    except Exception as e:
                        print(f"Warning: Failed to create membership period for {first_name}: {str(e)}")
                        error_details.append(
                            f"Row {reader.line_num} - Membership period failed for {first_name}: {str(e)}")

                # Role
                try:
                    PersonRole.objects.create(
                        person=person,
                        role_id=Role.MEMBER if has_active else Role.EXTERNAL
                    )
                    # print(f"person role {first_name} - {Role.MEMBER if has_active else Role.EXTERNAL}")
                except Exception as e:
                    print(f"Warning: Failed to assign role to {first_name}: {str(e)}")
                    error_details.append(f"Row {reader.line_num} - Role assignment failed for {first_name}: {str(e)}")

                imported_count += 1

            except Exception as e:
                skipped_count += 1
                error_details.append(f"Row {reader.line_num}: {str(e)}")
                print(f"Error processing row {reader.line_num}: {str(e)}")
                continue

    messages.success(request, f"Import complete: {imported_count} imported, {skipped_count} skipped")

    return {
        'success': True,
        'count': imported_count,
        'skipped': skipped_count,
        'errors': len(error_details),
        'error_details': error_details
    }



EVENT_INTERNAL_ID_KEY = "internal_id"
EVENT_NAME_KEY = "title"
EVENT_LOCATION_KEY = "location_city"
EVENT_LOCATION_RID_KEY = "location_rid"
EVENT_LOCATION_CUSTOM_KEY = "location_custom"
EVENT_STARTED_AT_KEY = "start_date"
EVENT_STARTED_AT_HOUR_KEY = "start_hour"
EVENT_ENDED_AT_KEY = "end_date"
EVENT_TYPE_KEY = "duration_rid"
EVENT_DETAILS_KEY = "description"
EVENT_NUM_VISITORS_KEY = "num_visitors"
EVENT_PROJECT_KEY = "project"

ALLOWED_EVENT_KEYS = [
    EVENT_INTERNAL_ID_KEY,
    EVENT_NAME_KEY,
    EVENT_LOCATION_KEY,
    EVENT_LOCATION_CUSTOM_KEY,
    EVENT_LOCATION_RID_KEY,
    EVENT_STARTED_AT_KEY,
    EVENT_ENDED_AT_KEY,
    EVENT_TYPE_KEY,
    EVENT_DETAILS_KEY,
    EVENT_NUM_VISITORS_KEY,
    EVENT_PROJECT_KEY,
    EVENT_STARTED_AT_HOUR_KEY,
]


def import_events(org_user, request, file_path, delimiter=";"):
    """Import events from CSV file."""
    imported_count = 0
    skipped_count = 0
    error_details = []

    # Check permissions
    if request.user != org_user:
        has_permission = AccessControl.can_edit_event(request.user, org_user).exists()
        if not has_permission:
            messages.error(request, "You don't have permission to import.")
            return {'success': False, 'count': 0, 'error': 'Permission denied'}

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        headers = reader.fieldnames
        print(headers)

        for h in headers:
            if h not in ALLOWED_EVENT_KEYS:
                return None

        for row in reader:
            try:
                # internal_id = (row.get(EVENT_INTERNAL_ID_KEY) or '').strip() or None
                name = (row.get(EVENT_NAME_KEY) or '').strip() or None
                location = (row.get(EVENT_LOCATION_KEY) or '').strip() or None
                started_at = (row.get(EVENT_STARTED_AT_KEY) or '').strip() or None
                started_hour = (row.get(EVENT_STARTED_AT_HOUR_KEY) or '').strip() or None
                ended_at = (row.get(EVENT_ENDED_AT_KEY) or '').strip() or None
                event_type = (row.get(EVENT_TYPE_KEY) or '').strip() or None
                details = (row.get(EVENT_DETAILS_KEY) or '').strip() or None
                num_visitors = (row.get(EVENT_NUM_VISITORS_KEY) or '').strip() or None
                project_title = (row.get(EVENT_PROJECT_KEY) or '').strip() or None

                Event.objects.create(
                    user=org_user,
                    # internal_id=internal_id,
                    name=name,
                    location=location,
                    started_at=started_at,
                    ended_at=ended_at,
                    event_type=event_type,
                    details=details,
                    num_visitors=num_visitors,
                )
                if project_title:
                    Project.objects.get_or_create(
                        title=project_title
                    )

                imported_count += 1

            except Exception as e:
                skipped_count += 1
                error_details.append(f"Row {reader.line_num}: {str(e)}")
                print(f"Error processing row {reader.line_num}: {str(e)}")
                continue

        return {
            'success': True,
            'count': imported_count
        }
