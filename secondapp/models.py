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



class Member(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    voice = models.CharField(max_length=10, choices=[(voice.name, voice.value) for voice in VoiceType])
    is_active = models.BooleanField(default=True)
    skill_level = models.CharField(max_length=20, choices=[(skill.name, skill.value) for skill in SkillLevel])
    phone_number = models.CharField(max_length=17, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    address = models.CharField(max_length=250, blank=True, null=True)
    date_of_birth = models.DateField("birthday", blank=True, null=True)
    messenger = models.CharField(max_length=250, blank=True, null=True)
    #photo =    ->    # to be added later
    shirt_size = models.CharField(max_length=4, choices=[(size.name, size.value) for size in ShirtSize])
    date_joined = models.DateField("joined",default=date.today)
    additional_member_notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["voice"]

    def __str__(self):
        return f"{self.first_name}, {self.last_name} - {self.voice}"


class Song(models.Model):
    title =  models.CharField(max_length=250)
    composer =  models.CharField(max_length=250)
    arranger = models.CharField(max_length=250)
    poet = models.CharField(max_length=250)

    class Meta:
        ordering = ["composer"]

    def __str__(self):
        return f"{self.title} - {self.composer}"


class Rehearsal(models.Model):
    subtitle = models.CharField(max_length=250)
    location = models.CharField(max_length=250)
    parking = models.CharField(max_length=250, blank=True, null=True)
    calendar = models.DateTimeField(blank=True, null=True, unique=True)
    additional_notes = models.TextField(blank=True, null=True)
    members = models.ManyToManyField(Member)
    songs = models.ManyToManyField(Song)

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
