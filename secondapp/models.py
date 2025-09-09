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
    SINGER = "Singer"
    COMPOSER = "Composer"
    ARRANGER = "Arranger"
    POET = "Poet"
    MUSICIAN = "Musician"


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
    phone_number = models.CharField(max_length=17, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    address = models.CharField(max_length=250, blank=True, null=True)
    birth_date = models.DateField("birthday", blank=True, null=True)
    death_date = models.DateField("death day", blank=True, null=True)
    nationality = models.CharField("nationality", max_length=100, blank=True, null=True)
    biography = models.TextField("short bio", blank=True, null=True)
    favorite_works = models.TextField(blank=True, null=True)
    influenced_by = models.TextField(blank=True, null=True)
    awards = models.TextField(blank=True, null=True)
    website = models.TextField(blank=True, null=True)
    #tags = models.ManyToManyField(Tag, help_text="max singers 5, others 3", blank=True)
    additional_notes = models.TextField(blank=True, null=True)
    # portrait =    ->    # TODO
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


class Singer(Person):
    voice = models.CharField(max_length=10, choices=[(voice.name, voice.value) for voice in VoiceType])
    is_active = models.BooleanField(default=True)
    skill_level = models.CharField(max_length=20, choices=[(skill.name, skill.value) for skill in SkillLevel])
    messenger = models.CharField(max_length=250, blank=True, null=True)
    shirt_size = models.CharField(max_length=4, choices=[(size.name, size.value) for size in ShirtSize], blank=True, null=True)
    date_joined = models.DateField("joined",default=date.today)

    class Meta(Person.Meta):
        ordering = ["voice", "last_name"]
        verbose_name = "Singer"
        verbose_name_plural = "Singers"

    def save(self, *args, **kwargs):
        self.role = Role.SINGER.name
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return  reverse("secondapp_singer_detail", kwargs={"pk": self.pk})

    def get_rehearsal_attendance(self):
        present_rehearsals = self.rehearsal_set.all()
        all_rehearsals = Rehearsal.objects.filter(is_cancelled=False)
        missing_rehearsals = all_rehearsals.exclude(pk__in=present_rehearsals)

        return {
            "present": present_rehearsals,
            "missing": missing_rehearsals,
        }

    def __str__(self):
        #max_tags = 5
        #tag_names = ", ".join(tag.name for tag in self.tags.all()[:max_tags])
        status = "(Inactive)" if not self.is_active else ""
        return f"{self.get_display_name()} - {self.voice} {status}"


class Composer(Person):
    work_style = models.CharField(max_length=250)
    musical_era = models.CharField(max_length=250, blank=True, null=True)
    instruments = models.CharField("favorite instruments", max_length=250)

    class Meta(Person.Meta):
        ordering = ["last_name", "first_name"]
        verbose_name = "Composer"
        verbose_name_plural = "Composers"

    def save(self, *args, **kwargs):
        self.role = Role.COMPOSER.name
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("secondapp:composer_detail", kwargs={"pk": self.pk})

    def __str__(self):
        #max_tags = 3
        #tag_names = ", ".join(tag.name for tag in self.tags.all()[:max_tags])
        era = f"{self.musical_era}" if self.musical_era else ""
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
        return reverse("secondapp:poet_detail", kwargs={"pk": self.pk})

    def __str__(self):
        #max_tags = 3
        #tag_names = ", ".join(tag.name for tag in self.tags.all()[:max_tags])
        return f"{self.get_display_name()}"


class Arranger(Person):
    style = models.CharField(max_length=250)
    instruments = models.CharField("favorite instruments", max_length=250)

    class Meta(Person.Meta):
        ordering = ["last_name", "first_name"]
        verbose_name = "Arranger"
        verbose_name_plural = "Arrangers"

    def save(self, *args, **kwargs):
        self.role = Role.ARRANGER.name
        super().save(*args, **kwargs)

    def get_abslute_url(self):
        return reverse("secondapp:arranger_detail", kwargs={"pk": self.pk})

    def __str__(self):
        #max_tags = 3
        #tag_names = ", ".join(tag.name for tag in self.tags.all()[:max_tags])
        return f"{self.get_display_name()}"


class Musician(Person):
    instrument = models.CharField("primary instrument", max_length=250)
    genre =  models.CharField("primary genre", max_length=250)
    #bands = models.ManyToManyField "active currently"
    #songs = models.ManyToManyField "best song performances"

    class Meta(Person.Meta):
        ordering = ["last_name", "first_name"]
        verbose_name = "Musician"
        verbose_name_plural = "Musicians"

    def save(self, *args, **kwargs):
        self.role = Role.MUSICIAN.name
        super().save(*args, **kwargs)

    def get_abslute_url(self):
        return reverse("secondapp:musician_detail", kwargs={"pk": self.pk})

    def __str__(self):
        #max_tags = 3
        #tag_names = ", ".join(tag.name for tag in self.tags.all()[:max_tags])
        return f"{self.get_display_name()} - {self.instrument}"


class Song(models.Model):
    title =  models.CharField(max_length=250)
    composer =  models.ForeignKey(Composer, on_delete=models.PROTECT,  related_name="songs", blank=True, null=True)
    arranger = models.ForeignKey(Arranger, on_delete=models.PROTECT,  related_name="songs", blank=True, null=True)
    poet = models.ForeignKey(Poet, on_delete=models.PROTECT,  related_name="songs", blank=True, null=True)
    genre = models.CharField(max_length=200, blank=True, null=True)
    tags = models.ManyToManyField(Tag, help_text="max 3", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["genre"]),
        ]

    def get_absolute_url(self):
        return reverse("secondapp:song_detail", kwargs={"pk": self.pk})

    def __str__(self):
        max_tags = 5
        tag_names = ", ".join(tag.name for tag in self.tags.all()[:max_tags])
        composer_name = self.composer.last_name if self.composer else "Unknown"
        genre_display = f"- {self.genre}" if self.genre else ""
        return f"{self.title} - {composer_name} - {genre_display} - {tag_names}"


class Rehearsal(models.Model):
    subtitle = models.CharField(max_length=250)
    location = models.CharField(max_length=250)
    parking = models.CharField(max_length=250, blank=True, null=True)
    calendar = models.DateTimeField(blank=True, null=True, unique=True)
    additional_notes = models.TextField(blank=True, null=True)
    singers = models.ManyToManyField(Singer, blank=True, related_name= "rehearsal_set")
    songs = models.ManyToManyField(Song, blank=True)
    tags = models.ManyToManyField(Tag, help_text="max 5", blank=True)
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

    def get_singer_count(self):
        return self.singers.count()

    def get_song_count(self):
        return self.songs.count()

    def get_absolute_url(self):
        return reverse("secondapp:rehearsal_detail", kwargs={"pk": self.pk})

    def get_singer_status(self):
        now = timezone.now()
        active_singers = Singer.objects.filter(is_active=True)
        present_singers = self.singers.all()
        missing_singers = active_singers.exclude(pk__in=present_singers)

        return {
            "present": present_singers,
            "missing": missing_singers,
        }

    def __str__(self):
        max_tags = 5
        tag_names = ", ".join(tag.name for tag in self.tags.all()[:max_tags])
        status = "(Cancelled)" if self.is_cancelled else ""
        calendar_display = self.calendar.strftime("%Y-%m-%d %H:%M") #if self.calendar else "TBD"
        return f"{calendar_display} - {self.subtitle} {status} - {tag_names}"

    # Song
    #  -> temporary out:
    #number_of_copies = models.IntegerField(validators=[MinValueValidator(1)])
    #number_of_pages = models.IntegerField(validators=[MinValueValidator(1)])
    #number_of_voices = models.IntegerField(validators=[MinValueValidator(1)])
    #song_difficulty_level =  models.CharField(max_length=20, choices=SkillLevel.choices, default=SkillLevel.EXPERIENCED)
    #transcript = models.TextField()
    #translation = models.TextField(blank=True, null=True)
    #speech_articulation = models.TextField(blank=True, null=True)
    #date_of_rehearsal = models.DateField("date of rehearsal")  # -> for later implementation
    #date_of_concert = models.ForeignKey(RehearsalDate, on_delete=models.PROTECT, related_name='song', blank=True, null=True) #, default=1 # -> for later implementation
    #date_added = models.DateField("added to archive", default=date.today)
    #additional_songs_notes = models.TextField(blank=True, null=True)
