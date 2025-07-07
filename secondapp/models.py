from random import choices

from django.db import models
import datetime
from datetime import date
from enum import Enum
from django.utils import timezone
from django.core.validators import MinValueValidator



class ShirtSize(Enum):
    XXS = '2x Extra Small'
    XS = 'Extra Small'
    S = 'Small'
    M = 'Medium'
    L = 'Large'
    XL = 'Extra Large'
    XXL = '2x Extra Large'
    XXXL = '3x Extra Large'


class VoiceType(models.TextChoices):
    SOPRANO1 = 'Soprano', 'Soprano'
    SOPRANO2 = 'Mezzo-Soprano', 'Mezzo-Soprano'
    ALTO1 = 'Higher-Alto', 'Higher-Alto'
    ALTO2 = 'Lower-Alto', 'Lower-Alto'
    CONTRAALTO = 'Contra-Alto', 'Contra-Alto'
    COUNTERTENOR = 'Counter-Tenor', 'Counter-Tenor'
    TENOR1 = 'Higher-Tenor', 'Higher-Tenor'
    TENOR2 = 'Lower-Tenor', 'Lower-Tenor'
    BARITONE = 'Baritone', 'Baritone'
    BASSO = 'Basso', 'Basso'
    CONTRABASSO = 'Contra-Basso', 'Contra-Basso'

class SkillLevel(models.TextChoices):
    BEGINNER = "Beginner", "Beginner"
    ENTHUSIAST = "Enthusiast", "Enthusiast"
    EXPERIENCED = "Experienced", "Experienced"
    SCHOOLED = "Schooled", "Schooled"
    PROFESSIONAL = "Professional", "Professional"

#class Attendance(models.TextChoices):
#    PRESENT = "Present", "Present"
#    ABSENT = "Absent", "Absent"
    #LATE = "Late", "Late"



class Attendee(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    instrument = models.CharField(max_length=12, choices=[(voice.name, voice.value) for voice in VoiceType])
    is_active = models.BooleanField(default=True)
    skill_level = models.CharField(max_length=20, choices=[(skill.name, skill.value) for skill in SkillLevel])
    phone_number = models.CharField(max_length=17, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    address = models.CharField(max_length=250, blank=True, null=True)
    date_of_birth = models.DateField("birthday")
    messenger = models.CharField(max_length=250, blank=True, null=True)
    #photo =    ->    # to be added later
    shirt_size = models.CharField(max_length=4, choices=[(size.name, size.value) for size in ShirtSize])
    date_of_joining = models.DateField("joined",default=date.today)
    additional_attendee_notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["instrument"]

    def __str__(self):
        return f"{self.first_name}, {self.last_name} - {self.instrument}" #get_instrument_display()}"


class RehearsalDate(models.Model):
    rehearsal_subtitle = models.CharField(max_length=250)
    rehearsal_location = models.CharField(max_length=250)
    rehearsal_location_parking = models.CharField(max_length=250, blank=True, null=True)
    rehearsal_calendar = models.DateTimeField(blank=True, null=True, unique=True)
    additional_rehearsal_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.rehearsal_calendar} - {self.rehearsal_subtitle}"

    def generate_date_url(self):
        return format(self.rehearsal_calendar, "Y-m-d")


class AttendanceRecord(models.Model):
    present = models.BooleanField()    # -> this one has to be tested again
    date_record = models.ForeignKey(RehearsalDate, on_delete=models.CASCADE,related_name="attendance_records")
    attendees = models.ManyToManyField(Attendee,through="AttendanceDetail")

    class Meta:
        ordering = ["date_record"]

    def __str__(self):
        return f"Attendance on {self.date_record}"


class AttendanceDetail(models.Model):
    attendee = models.ForeignKey(Attendee, on_delete=models.PROTECT, related_name="attendance_detail")
    attendance_record = models.ForeignKey(AttendanceRecord, on_delete=models.CASCADE, related_name="attendance_detail")
    additional_attendance_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.attendee} - {self.attendance_record}"



    # "{self.rehearsal_location}"

    #def formatted_rehearsal_date(self):
    #    return self.rehearsal_calendar

    #def formatted_rehearsal_location(self):
    #    return f"{self.rehearsal_location},{self.rehearsal_location_parking}"

    #def formatted_rehearsal_subtitle(self):
    #    return f"{self.rehearsal_subtitle}"

class Song(models.Model):
    song_title =  models.CharField(max_length=250)
    song_composer =  models.CharField(max_length=250)
    song_author = models.CharField(max_length=250)
    song_genre =  models.CharField(max_length=250)
    number_of_copies = models.IntegerField(validators=[MinValueValidator(1)])
    number_of_pages = models.IntegerField(validators=[MinValueValidator(1)])
    number_of_voices = models.IntegerField(validators=[MinValueValidator(1)])
    song_difficulty_level =  models.CharField(max_length=20, choices=SkillLevel.choices, default=SkillLevel.EXPERIENCED)
    transcript = models.TextField()
    translation = models.TextField(blank=True, null=True)
    speech_articulation = models.TextField(blank=True, null=True)
    #date_of_rehearsal = models.DateField("date of rehearsal")  # -> for later implementation
    #date_of_concert = models.ForeignKey(RehearsalDate, on_delete=models.PROTECT, related_name='song', blank=True, null=True) #, default=1 # -> for later implementation
    date_added = models.DateField("added to archive", default=date.today)
    additional_songs_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.song_title} - {self.song_composer}"



class CurrentRehearsal(models.Model):    # -> this is temporary out - to be remade later

    rehearsal = models.ForeignKey(RehearsalDate, on_delete=models.CASCADE, related_name='current_rehearsals', default=1)  # Default to the default_rehearsal
    #attendance = models.CharField(max_length=9, choices=Attendance.choices)    # temporary out!
    #song = models.ForeignKey(Song, on_delete=models.PROTECT, related_name='current_rehearsals')
    #attendee = models.ForeignKey(Attendee, on_delete=models.PROTECT, related_name='current_rehearsals')    # temporary out!

    #def save(self, *args, **kwargs):
    #    if not self.rehearsal_id:
    #        default_rehearsal = RehearsalDate.objects.create(
    #            rehearsal_subtitle = "DefaultRehearsal",
    #            rehearsal_location = "Usual Location",
    #            rehearsal_location_parking = "",
    #            rehearsal_calendar = timezone.now(),
    #            additional_rehearsal_notes = "This is the default rehearsal"
    #        )
    #        self.rehearsal = default_rehearsal
    #    super().save()

    def __str__(self):
        return f"{self.rehearsal}"# - {self.attendee} - {self.get_attendance_display()}"  # —> for a test I comment this out
