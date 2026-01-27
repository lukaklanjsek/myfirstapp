
from django.db import models
from django.db.models import PROTECT, CASCADE
from django.db import transaction
from django.urls import reverse
import datetime
from datetime import date
from enum import Enum
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.conf import settings


#class VoiceType(Enum):
#    Soprano = 'Soprano'
#    Alto = 'Alto'
#    Tenor = 'Tenor'
#    Bass = 'Bass'




#class Role(Enum):
#    MEMBER = "member"
#    COMPOSER = "composer"
#    ARRANGER = "arranger"
#    POET = "poet"
#    MUSICIAN = "musician"
#    CONDUCTOR = "conductor"


class Group(Enum):
    MIXED = "mixed"
    FEMALE = "female"
    MALE = "male"


#class Position(Enum):
#    STAFF = "staff"
#    PARTICIPANT = "participant"

class Role(Enum):
    ADMIN = "admin"
    MEMBER = "member"
    SUPPORTER = "supporter"

#class Tag(models.Model):
#    name = models.CharField(max_length=100, unique=True)
#    date_added = models.DateField(auto_now_add=True)

#    created_at = models.DateTimeField(auto_now_add=True)
#    updated_at = models.DateTimeField(auto_now=True)

#    class Meta:
#        ordering = ["name"]

#    def __str__(self):
#        return self.name


class AuthUser(AbstractUser):
    """Global auth. User is only login. Identity is through Person. Organization is context."""
#    email = models.EmailField(unique=True)
#    phone_number = models.CharField(max_length=19, blank=True, null=True)
    first_name = None
    last_name = None    # override to make them unused, hidden

    # REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username


class Organization(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Person(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone =  models.CharField(max_length=23, blank=True, null=True)
    birth_date = models.DateField("birthday", blank=True, null=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="persons"
    )

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Membership(models.Model):
    """Base relationship between Person and Organization."""
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="memberships")
    person = models.ForeignKey(Person, on_delete=models.PROTECT, related_name="memberships")
    role = models.CharField(max_length=15, choices=[(role.name, role.value) for role in Role])
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "person", "role"],
                name="unique_membership_per_org_person"
            )
        ]


class MembershipPeriod(models.Model):
    """Tracks activity periods for each role assignment."""
    membership = models.ForeignKey(Membership, on_delete=models.PROTECT, related_name="periods")
    started_at = models.DateField(auto_now_add=True)
    ended_at = models.DateField(null=True, blank=True)


# class Status(models.Model):
#    """Catalogue of possible profile attributes.
#    Ex. admin, member, supporter"""
#    key = models.CharField(max_length=50, unique=True)
#    label = models.CharField(max_length=255)
#
#    def __str__(self):
#        return self.label
#
#
# class OrganizationProfile(models.Model):
#    """Through model between org and user."""
#    organization = models.ForeignKey(
#        Organization,
#        on_delete=models.CASCADE,
#        related_name="profiles"
#    )
#
#         related_name="profiles"
#     )
#     display_name = models.CharField(max_length=255)
#
#     class Meta:
#         constraints = [
#             models.UniqueConstraint(
#                 fields=["organisation", "user"],
#                 condition=models.Q(user__isnull=False),
#                 name="unique_user_profile_per_org",
#             )
#         ]
#
#     def __str__(self):
#         return f"{self.display_name} @ {self.organisation}"
#
#     def get_status(self, key) -> Optional[bool]:
#         """True/False is explicitly existing"""
#         try:
#             return self.statuses.get(status__key=key).value
#         except ProfileStatus.DoesNotExist:
#             return None
#
#     def has_status(self, key: str) -> bool:
#         """Checks if status True"""
#         return self.get_status(key) is True
#
#     def set_status(self, key, value: bool):
#         """ Set status True/False.
#         If value=None, deletes status."""
#         status_obj, _ = Status.objects.get_or_create(key=key, defaults={"label": key})
#
#         if value is None:
#             self.statuses.filter(status=status_obj).delete()
#         else:
#             ProfileStatus.objects.update_or_create(
#                 profile=self,
#                 status=status_obj,
#                 defaults={"value": value},
#             )
#
#
# class ProfileStatus(models.Model):
#     """Through model for status and org-profile."""
#     profile = models.ForeignKey(
#         OrganisationProfile,
#         on_delete=models.CASCADE,
#         related_name="statuses"
#     )
#     status = models.ForeignKey(
#         Status,
#         on_delete=models.CASCADE,
#         related_name="profile_values"
#     )
#     active = models.BooleanField(
#         null=True,
#         help_text="NULL = not defined, True = yes, False = no"
#     )
#
#     class Meta:
#         unique_together = ("profile", "status")
#
#     def __str__(self):
#         return f"{self.profile} :: {self.status.key} = {self.value}"
#
#
# class Person(models.Model):
#     first_name = models.CharField(max_length=100, blank=True, null=True)
#     last_name = models.CharField(max_length=100, db_index=True, blank=True, null=True)
#
#     role = models.CharField(max_length=10, choices=[(role.name, role.value) for role in Role])
#     address = models.CharField(max_length=250, blank=True, null=True)
#     email = models.EmailField(blank=True, null=True)
#     phone_number = models.CharField(max_length=17, blank=True, null=True)
#     mobile_number = models.CharField(max_length=17, blank=True, null=True)
#     birth_date = models.DateField("birthday", blank=True, null=True)
#
#     additional_notes = models.TextField(blank=True, null=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         abstract = True
#         indexes = [
#             models.Index(fields=["last_name"]),
#             models.Index(fields=["role"]),
#         ]
#
#     def get_full_name(self):
#         names = [self.first_name, self.last_name]
#
#         return " ".join(names)
#
#     def get_display_name(self):
#         display_name = f"{self.last_name}, {self.first_name}"
#
#         return display_name
#
#     def get_role_name(self):
#         return self.__class__.__name__.lower()
#
#
# class Member(Person):
#     voice = models.CharField(max_length=10, choices=[(voice.name, voice.value) for voice in VoiceType])
#     is_active = models.BooleanField(default=True)
#     date_active = models.TextField("date_active", blank=True, null=True)
#
#     class Meta(Person.Meta):
#         ordering = ["voice", "last_name"]
#         verbose_name = "Member"
#         verbose_name_plural = "Members"
#
#     def save(self, *args, **kwargs):
#         self.role = Role.MEMBER.name
#         super().save(*args, **kwargs)
#
#     def get_absolute_url(self):
#         return  reverse("secondapp:person_detail", kwargs={"role": "member", "pk": self.pk})
#
#     def get_rehearsal_attendance(self):
#         present_rehearsals = self.rehearsals.all()
#         all_rehearsals = Rehearsal.objects.filter(is_cancelled=False)
#         missing_rehearsals = all_rehearsals.exclude(pk__in=present_rehearsals)
#
#         return {
#             "present": present_rehearsals,
#             "missing": missing_rehearsals,
#         }
#
#     def __str__(self):
#         status = "(Inactive)" if not self.is_active else ""
#         voice_display = self.get_voice_display()  # This gets the human-readable value
#         return f"{self.get_display_name()} - {voice_display} {status}"
#
#
# class Composer(Person):
#     musical_era = models.CharField(max_length=250, blank=True, null=True)
#
#     class Meta(Person.Meta):
#         ordering = ["last_name", "first_name"]
#         verbose_name = "Composer"
#         verbose_name_plural = "Composers"
#
#     def save(self, *args, **kwargs):
#         self.role = Role.COMPOSER.name
#         super().save(*args, **kwargs)
#
#     def get_absolute_url(self):
#         return reverse("secondapp:person_detail", kwargs={"role": "composer", "pk": self.pk})
#
#     def __str__(self):
#         return f"{self.get_display_name()}"
#
#
# class Poet(Person):
#     writing_style =  models.CharField(max_length=250, blank=True, null=True)
#     literary_style = models.CharField(max_length=250, blank=True, null=True)
#
#     class Meta(Person.Meta):
#         ordering = ["last_name", "first_name"]
#         verbose_name = "Poet"
#         verbose_name_plural = "Poets"
#
#     def save(self, *args, **kwargs):
#         self.role = Role.POET.name
#         super().save(*args, **kwargs)
#
#     def get_absolute_url(self):
#         return reverse("secondapp:person_detail", kwargs={"role": "poet", "pk": self.pk})
#
#     def __str__(self):
#         return f"{self.get_display_name()}"
#
#
# class Arranger(Person):
#     style = models.CharField(max_length=250)
#
#     class Meta(Person.Meta):
#         ordering = ["last_name", "first_name"]
#         verbose_name = "Arranger"
#         verbose_name_plural = "Arrangers"
#
#     def save(self, *args, **kwargs):
#         self.role = Role.ARRANGER.name
#         super().save(*args, **kwargs)
#
#     def get_absolute_url(self):
#         return reverse("secondapp:person_detail", kwargs={"role": "arranger", "pk": self.pk})
#
#     def __str__(self):
#         return f"{self.get_display_name()}"
#
#
# class Musician(Person):
#     instrument = models.CharField("primary instrument", max_length=250)
#
#     class Meta(Person.Meta):
#         ordering = ["last_name", "first_name"]
#         verbose_name = "Musician"
#         verbose_name_plural = "Musicians"
#
#     def save(self, *args, **kwargs):
#         self.role = Role.MUSICIAN.name
#         super().save(*args, **kwargs)
#
#     def get_absolute_url(self):
#         return reverse("secondapp:person_detail", kwargs={"role": "musician", "pk": self.pk})
#
#     def __str__(self):
#         return f"{self.get_display_name()} - {self.instrument}"
#

# class Conductor(Person):
#    is_active = models.BooleanField(default=True)
#    messenger = models.CharField(max_length=250, blank=True, null=True)
#    date_joined = models.DateField("joined",default=date.today)
#
#    class Meta(Person.Meta):
#        ordering = ["last_name", "first_name"]
#        verbose_name = "Conductor"
#        verbose_name_plural = "Conductors"
#
#    def save(self, *args, **kwargs):
#        self.role = Role.CONDUCTOR.name
#        super().save(*args, **kwargs)
#
#    def get_absolute_url(self):
#        return reverse("secondapp:person_detail", kwargs={"role": "conductor", "pk": self.pk})
#
#    def get_rehearsal_attendance(self):
#        present_rehearsals = self.rehearsals.all()
#        all_rehearsals = Rehearsal.objects.filter(is_cancelled=False)
#        missing_rehearsals = all_rehearsals.exclude(pk__in=present_rehearsals)
#
#        return {
#            "present": present_rehearsals,
#            "missing": missing_rehearsals,
#        }
#
#    def __str__(self):
#        return f"{self.get_display_name()}"
#
#
# class Song(models.Model):
#     id = models.IntegerField(primary_key=True)
#     title =  models.CharField(max_length=250)
#     composer =  models.ForeignKey(Composer, on_delete=models.PROTECT,  related_name="song", blank=True, null=True)
#     poet = models.ForeignKey(Poet, on_delete=models.PROTECT,  related_name="song", blank=True, null=True)
#     number_of_pages = models.IntegerField(blank=True, null=True)
#     number_of_copies = models.IntegerField(blank=True, null=True)
#     year = models.IntegerField("year of creation", blank=True, null=True)
#     group = models.CharField(max_length=15, choices=[(group.name, group.value) for group in Group])
#     number_of_voices = models.IntegerField(blank=True, null=True)
#     additional_notes = models.TextField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     class Meta:
#         ordering = ["title"]
#         indexes = [
#             models.Index(fields=["title"]),
#         ]
#
#     def get_absolute_url(self):
#         return reverse("secondapp:song_detail", kwargs={"pk": self.pk})
#
#     def __str__(self):
#         composer_name = self.composer.last_name if self.composer else "Unknown"
#         return f"{self.title} - {composer_name}"
#
#
# class Rehearsal(models.Model):
#     calendar = models.DateTimeField(unique=True)
#     additional_notes = models.TextField(blank=True, null=True)
#     members = models.ManyToManyField(Member, blank=True, related_name= "rehearsals")
#     conductors = models.ManyToManyField(Conductor, blank=True, related_name= "rehearsals")
#     songs = models.ManyToManyField(Song, blank=True, related_name= "rehearsals")
#     is_cancelled = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     class Meta:
#         verbose_name_plural = "Rehearsals"
#         ordering = ["-calendar"]
#         indexes = [
#             models.Index(fields=["calendar"]),
#             models.Index(fields=["is_cancelled"]),
#         ]
#
#     def recent(self):
#         return self.calendar >= timezone.now() - datetime.timedelta()
#
#     def is_upcoming(self):
#         if self.calendar:
#             return self.calendar > timezone.now()
#         return False
#
#     def get_member_count(self):
#         return self.members.count()
#
#     def get_song_count(self):
#         return self.songs.count()
#
#     def get_absolute_url(self):
#         return reverse("secondapp:rehearsal_detail", kwargs={"pk": self.pk})
#
#     def get_member_status(self):
#         now = timezone.now()
#         active_members = Member.objects.filter(is_active=True)
#         present_members = self.members.all()
#         missing_members = active_members.exclude(pk__in=present_members)
#
#         return {
#             "present": present_members,
#             "missing": missing_members,
#         }
#
#     def __str__(self):
#         status = "(Cancelled)" if self.is_cancelled else ""
#         calendar_display = self.calendar.strftime("%Y-%m-%d %H:%M")
#         return f"{calendar_display} - {status}"
#

# class Ensemble(models.Model):
#     name = models.CharField(max_length=250)
#     address = models.TextField()
#     additional_notes = models.TextField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     def __str__(self):
#         return f"{self.name}"


# class Activity(models.Model):
#     start_date = models.DateField(blank=True, null=True)
#     end_date = models.DateField(blank=True, null=True)
#     member = models.ForeignKey(Member, null=True, blank=True, on_delete=models.PROTECT, related_name="activity")
#     conductor = models.ForeignKey(Conductor, null=True, blank=True, on_delete=models.PROTECT, related_name="activity")
#     ensemble = models.ForeignKey(Ensemble, null=True, blank=True, on_delete=models.PROTECT, related_name="activity")
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     class Meta:
#         ordering = ["start_date"]
#
#     def __str__(self):
#         return f"{self.member.first_name} {self.member.last_name} - {self.ensemble.name}: {self.start_date} - {self.end_date}"
#
#     def get_absolute_url(self):     # this is supposed to point back to the person
#         if self.member:
#             role = "member"
#             person = self.member
#         elif self.conductor:
#             role = "conductor"
#             person = self.conductor
#         else:
#             return "/"
#
#         return reverse("secondapp:person_detail", kwargs={"role": role, "pk": person.pk})
#
#
# class ImportFile(models.Model):
#     title = models.CharField(max_length=250)
#     file = models.FileField(upload_to="imports/")
#     updated_at = models.DateTimeField(auto_now=True)