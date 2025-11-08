from random import choices

from django.db import models
from django.urls import reverse
import datetime
from datetime import date
from enum import Enum
from django.utils import timezone
#from django.forms import ModelMultipleChoiceField
from django.core.exceptions import ValidationError




class ShirtSize(Enum):
    XXS = '2x Extra Small'
    XS = 'Extra Small'
    S = 'Small'
    M = 'Medium'
    L = 'Large'
    XL = 'Extra Large'
    XXL = '2x Extra Large'
    XXXL = '3x Extra Large'


class VoiceType(Enum):
    SOPRANO = 'Soprano'
    ALTO = 'Alto'
    TENOR = 'Tenor'
    BASS = 'Bass'


class SkillLevel(Enum):
    BEGINNER = "Beginner"
    ENTHUSIAST = "Enthusiast"
    EXPERIENCED = "Experienced"
    SCHOOLED = "Schooled"
    PROFESSIONAL = "Professional"


class Role(Enum):
    MEMBER = "Member"
    COMPOSER = "Composer"
    ARRANGER = "Arranger"
    POET = "Poet"
    MUSICIAN = "Musician"
    CONDUCTOR = "Conductor"


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    date_added = models.DateField(auto_now_add=True)
    # this might clash between all stamps but right now doing update for the footer
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Person(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, db_index=True)
    third_name = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=10, choices=[(role.name, role.value) for role in Role])
    address = models.CharField(max_length=250, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone_number = models.CharField(max_length=17, blank=True, null=True)
    mobile_number = models.CharField(max_length=17, blank=True, null=True)
    birth_date = models.DateField("birthday", blank=True, null=True)
#    death_date = models.DateField("death day", blank=True, null=True)
#    nationality = models.CharField("nationality", max_length=100, blank=True, null=True)
#    biography = models.TextField("short bio", blank=True, null=True)
#    favorite_works = models.TextField(blank=True, null=True)
#    influenced_by = models.TextField(blank=True, null=True)
#    awards = models.TextField(blank=True, null=True)
#    website = models.TextField(blank=True, null=True)
    additional_notes = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["last_name"]),
            models.Index(fields=["role"]),
        ]

    def get_full_name(self):
        names = [self.first_name, self.last_name]
        if self.third_name:
            names.insert(1, self.third_name)
        return " ".join(names)

    def get_display_name(self):
        display_name = f"{self.last_name}, {self.first_name}"
        if self.third_name:
            display_name += f" {self.third_name}"
        return display_name

    def get_role_name(self):
        return self.__class__.__name__.lower()


class Member(Person):
    voice = models.CharField(max_length=10, choices=[(voice.name, voice.value) for voice in VoiceType])
    is_active = models.BooleanField(default=True)
#    skill_level = models.CharField(max_length=20, choices=[(skill.name, skill.value) for skill in SkillLevel])
#    messenger = models.CharField(max_length=250, blank=True, null=True)
#    shirt_size = models.CharField(max_length=4, choices=[(size.name, size.value) for size in ShirtSize], blank=True, null=True)
    date_active = models.TextField("date_active", blank=True, null=True)

    class Meta(Person.Meta):
        ordering = ["voice", "last_name"]
        verbose_name = "Member"
        verbose_name_plural = "Members"

    def save(self, *args, **kwargs):
        self.role = Role.MEMBER.name
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return  reverse("secondapp:person_detail", kwargs={"role": "member", "pk": self.pk})

    def get_rehearsal_attendance(self):
        present_rehearsals = self.rehearsal_set.all()
        all_rehearsals = Rehearsal.objects.filter(is_cancelled=False)
        missing_rehearsals = all_rehearsals.exclude(pk__in=present_rehearsals)

        return {
            "present": present_rehearsals,
            "missing": missing_rehearsals,
        }

    def __str__(self):
        status = "(Inactive)" if not self.is_active else ""
        return f"{self.get_display_name()} - {self.voice} {status}"


class Composer(Person):
    musical_era = models.CharField(max_length=250, blank=True, null=True)

    class Meta(Person.Meta):
        ordering = ["last_name", "first_name"]
        verbose_name = "Composer"
        verbose_name_plural = "Composers"

    def save(self, *args, **kwargs):
        self.role = Role.COMPOSER.name
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("secondapp:person_detail", kwargs={"role": "composer", "pk": self.pk})

    def __str__(self):
        return f"{self.get_display_name()}"


class Poet(Person):
    writing_style =  models.CharField(max_length=250)
    literary_style = models.CharField(max_length=250)

    class Meta(Person.Meta):
        ordering = ["last_name", "first_name"]
        verbose_name = "Poet"
        verbose_name_plural = "Poets"

    def save(self, *args, **kwargs):
        self.role = Role.POET.name
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("secondapp:person_detail", kwargs={"role": "poet", "pk": self.pk})

    def __str__(self):
        return f"{self.get_display_name()}"


class Arranger(Person):
    style = models.CharField(max_length=250)

    class Meta(Person.Meta):
        ordering = ["last_name", "first_name"]
        verbose_name = "Arranger"
        verbose_name_plural = "Arrangers"

    def save(self, *args, **kwargs):
        self.role = Role.ARRANGER.name
        super().save(*args, **kwargs)

    def get_abslute_url(self):
        return reverse("secondapp:person_detail", kwargs={"role": "arranger", "pk": self.pk})

    def __str__(self):
        return f"{self.get_display_name()}"


class Musician(Person):
    instrument = models.CharField("primary instrument", max_length=250)

    class Meta(Person.Meta):
        ordering = ["last_name", "first_name"]
        verbose_name = "Musician"
        verbose_name_plural = "Musicians"

    def save(self, *args, **kwargs):
        self.role = Role.MUSICIAN.name
        super().save(*args, **kwargs)

    def get_abslute_url(self):
        return reverse("secondapp:person_detail", kwargs={"role": "musician", "pk": self.pk})

    def __str__(self):
        return f"{self.get_display_name()} - {self.instrument}"


class Conductor(Person):
    is_active = models.BooleanField(default=True)
    messenger = models.CharField(max_length=250, blank=True, null=True)
    date_joined = models.DateField("joined",default=date.today)

    class Meta(Person.Meta):
        ordering = ["last_name", "first_name"]
        verbose_name = "Conductor"
        verbose_name_plural = "Conductors"

    def save(self, *args, **kwargs):
        self.role = Role.CONDUCTOR.name
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("secondapp:person_detail", kwargs={"role": "conductor", "pk": self.pk})

    def get_rehearsal_attendance(self):
        present_rehearsals = self.rehearsal_set.all()
        all_rehearsals = Rehearsal.objects.filter(is_cancelled=False)
        missing_rehearsals = all_rehearsals.exclude(pk__in=present_rehearsals)

        return {
            "present": present_rehearsals,
            "missing": missing_rehearsals,
        }

    def __str__(self):
        return f"{self.get_display_name()}"


class Song(models.Model):
    title =  models.CharField(max_length=250)
    composer =  models.ForeignKey(Composer, on_delete=models.PROTECT,  related_name="songs", blank=True, null=True)
    poet = models.ForeignKey(Poet, on_delete=models.PROTECT,  related_name="songs", blank=True, null=True)
    number_of_pages = models.IntegerField(blank=True, null=True)
    number_of_copies = models.IntegerField(blank=True, null=True)
    year = models.DateField("year of creation", blank=True, null=True)
    group = models.CharField("mixed/male/female" , max_length=250, blank=True, null=True)
    number_of_voices = models.IntegerField(blank=True, null=True)
    additional_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        indexes = [
            models.Index(fields=["title"]),
        ]

    def get_absolute_url(self):
        return reverse("secondapp:song_detail", kwargs={"pk": self.pk})

    def __str__(self):
        composer_name = self.composer.last_name if self.composer else "Unknown"
        return f"{self.title} - {composer_name}"


class Rehearsal(models.Model):
    subtitle = models.CharField(max_length=250)
    location = models.CharField(max_length=250)
    parking = models.CharField(max_length=250, blank=True, null=True)
    calendar = models.DateTimeField(unique=True)
    additional_notes = models.TextField(blank=True, null=True)
    members = models.ManyToManyField(Member, blank=True, related_name= "rehearsal_set")
    conductors = models.ManyToManyField(Conductor, blank=True, related_name="rehearsal_set")
    songs = models.ManyToManyField(Song, blank=True)
    duration_minutes = models.PositiveIntegerField(blank=True, null=True, help_text="Expected duration in minutes")
    attendance_count = models.PositiveIntegerField(default=0, help_text="Actual attendance count")
    is_cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Rehearsals"
        ordering = ["-calendar"]
        indexes = [
            models.Index(fields=["calendar"]),
            models.Index(fields=["is_cancelled"]),
        ]

    def recent(self):
        return self.calendar >= timezone.now() - datetime.timedelta()

    def is_upcoming(self):
        if self.calendar:
            return self.calendar > timezone.now()
        return False

    def get_member_count(self):
        return self.members.count()

    def get_song_count(self):
        return self.songs.count()

    def get_absolute_url(self):
        return reverse("secondapp:rehearsal_detail", kwargs={"pk": self.pk})

    def get_member_status(self):
        now = timezone.now()
        active_members = Member.objects.filter(is_active=True)
        present_members = self.members.all()
        missing_members = active_members.exclude(pk__in=present_members)

        return {
            "present": present_members,
            "missing": missing_members,
        }

    def __str__(self):
        status = "(Cancelled)" if self.is_cancelled else ""
        calendar_display = self.calendar.strftime("%Y-%m-%d %H:%M") #if self.calendar else "TBD"
        return f"{calendar_display} - {self.subtitle} {status}"


class Ensemble(models.Model):
    name = models.CharField(max_length=250)
    address = models.TextField()
    additional_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"


class Activity(models.Model):
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    member = models.ForeignKey(Member, null=True, blank=True, on_delete=models.PROTECT, related_name="activity")
    conductor = models.ForeignKey(Conductor, null=True, blank=True, on_delete=models.PROTECT, related_name="activity")
    ensemble = models.ForeignKey(Ensemble, on_delete=models.PROTECT, related_name="activity")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):     # this is supposed to point back to the person
        if self.member:
            role = "member"
            person = self.member
        elif self.conductor:
            role = "conductor"
            person = self.conductor
        else:
            return "/"

        return reverse("secondapp:person_detail", kwargs={"role": role, "pk": person.pk})


class ImportFile(models.Model):
    title = models.CharField(max_length=250)
    file = models.FileField(upload_to="imports/")
    updated_at = models.DateTimeField(auto_now=True)