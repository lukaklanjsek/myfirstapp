from random import choices

from django.db import models
#import datetime
from datetime import date
from enum import Enum
#from django.utils import timezone
#from django.forms import ModelMultipleChoiceField




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

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return {self.name}


class Person(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, db_index=True)
    third_name = models.CharField(max_length=100, blank=True, null=True)
    #  TODO: make "role" no longer selectable within other models
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
    tags = models.ManyToManyField(Tag, blank=True)
    additional_notes = models.TextField(blank=True, null=True)
    # portrait =    ->    # TODO
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Singer(Person):
    voice = models.CharField(max_length=10, choices=[(voice.name, voice.value) for voice in VoiceType])
    is_active = models.BooleanField(default=True)
    skill_level = models.CharField(max_length=20, choices=[(skill.name, skill.value) for skill in SkillLevel])
    messenger = models.CharField(max_length=250, blank=True, null=True)
    shirt_size = models.CharField(max_length=4, choices=[(size.name, size.value) for size in ShirtSize], blank=True, null=True)
    date_joined = models.DateField("joined",default=date.today)

    class Meta(Person.Meta):
        ordering = ["voice"]

    def save(self, *args, **kwargs):
        self.role = Role.SINGER.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name}, {self.last_name} {self.third_name} - {self.voice}"


class Composer(Person):
    work_style = models.CharField(max_length=250)
    musical_era = models.CharField(max_length=250)
    instruments = models.CharField("favorite instruments", max_length=250)

    def save(self, *args, **kwargs):
        self.role = Role.COMPOSER.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name}, {self.last_name} {self.third_name} - {self.musical_era}"


class Poet(Person):
    writing_style =  models.CharField(max_length=250)
    literary_style = models.CharField(max_length=250)

    def save(self, *args, **kwargs):
        self.role = Role.POET.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name}, {self.last_name} {self.third_name}"


class Arranger(Person):
    style = models.CharField(max_length=250)
    instruments = models.CharField("favorite instruments", max_length=250)

    def save(self, *args, **kwargs):
        self.role = Role.ARRANGER.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name}, {self.last_name} {self.third_name} - {self.style}"


class Musician(Person):
    instrument = models.CharField("primary instrument", max_length=250)
    genre =  models.CharField("primary genre", max_length=250)
    #bands = models.ManyToManyField "active currently"
    #songs = models.ManyToManyField "best song performances"

    def save(self, *args, **kwargs):
        self.role = Role.MUSICIAN.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name}, {self.last_name} {self.third_name} - {self.instrument}"


class Song(models.Model):
    title =  models.CharField(max_length=250)
    composer =  models.ForeignKey(Composer, on_delete=models.PROTECT, related_name="song")
    arranger = models.ForeignKey(Arranger, on_delete=models.PROTECT, related_name="song")
    poet = models.ForeignKey(Poet, on_delete=models.PROTECT, related_name="song")
    tags = models.ManyToManyField(Tag, blank=True)

#    class Meta:
#        ordering = ["composer"]    # temporary out to see if we still need it

    def __str__(self):
        return f"{self.title} - {self.composer}"


class Rehearsal(models.Model):
    subtitle = models.CharField(max_length=250)
    location = models.CharField(max_length=250)
    parking = models.CharField(max_length=250, blank=True, null=True)
    calendar = models.DateTimeField(blank=True, null=True, unique=True)
    additional_notes = models.TextField(blank=True, null=True)
    singers = models.ManyToManyField(Singer)
    songs = models.ManyToManyField(Song)
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return f"{self.calendar} - {self.subtitle}"

    # Song
    #  -> temporary out:
    #genre =  models.CharField(max_length=250)
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
