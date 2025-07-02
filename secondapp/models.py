from django.db import models
from datetime import date
from enum import Enum
from django.utils import timezone



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
    S1 = 'Soprano'
    MS = 'Mezzo-Soprano'
    A1 = 'Higher-Alto'
    A2 = 'Lower-Alto'
    CA = 'Contra-Alto'
    CT = 'Counter-Tenor'
    T1 = 'Higher-Tenor'
    T2 = 'Lower-Tenor'
    B1 = 'Baritone'
    B2 = 'Bass'
    CB = 'Contra-Bass'

class SkillLevel(models.TextChoices):
    BEGINNER = "Beginner", "Beginner"
    ENTHUSIAST = "Enthusiast", "Enthusiast"
    EXPERIENCED = "Experienced", "Experienced"
    SCHOOLED = "Schooled", "Schooled"
    PROFESSIONAL = "Professional", "Professional"

class Attendee(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    instrument = models.CharField(max_length=2, choices=[(voice.name, voice.value) for voice in VoiceType])
    is_active = models.BooleanField(default=True)
    skill_level = models.CharField(max_length=20, choices=SkillLevel.choices,default=SkillLevel.ENTHUSIAST)
    phone_number = models.CharField(max_length=17, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    address = models.CharField(max_length=250, blank=True, null=True)
    date_of_birth = models.DateField("birthday")
    messenger = models.CharField(max_length=250, blank=True)
    #photo =    ->    # to be added later
    shirt_size = models.CharField(max_length=4, choices=[(size.name, size.value) for size in ShirtSize])
    date_of_joining = models.DateField("joined",default=date.today)
    additional_attendee_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} {self.get_instrument_display()}"

class Song(models.Model):
    # choices within Songs class:
    #DIFFICULTY_LEVEL = [
    #    ("1", "Beginner"),
    #    ("2", "Enthusiast"),
    #    ("3", "Experienced"),
    #    ("4", "Schooled"),
    #    ("5", "Professional"),
    #]
    song_title =  models.CharField(max_length=250)
    song_composer =  models.CharField(max_length=250)
    song_author = models.CharField(max_length=250)
    song_genre =  models.CharField(max_length=250)
    number_of_copies = models.CharField(max_length=4)
    number_of_pages = models.CharField(max_length=4)
    number_of_voices = models.CharField(max_length=4)
    song_difficulty_level =  models.CharField(max_length=20, choices=SkillLevel.choices, default=SkillLevel.EXPERIENCED)
    transcript = models.TextField()
    translation = models.TextField(blank=True)
    speech_articulation = models.TextField(blank=True)
    # date_of_rehearsal = models.DateField("date of rehearsal")
    date_of_concert = models.DateField("date of concert", blank=True)
    date_added = models.DateField("added to archive", default=date.today)
    additional_songs_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.song_title} {self.song_composer}"


class RehearsalDate(models.Model):
    rehearsal_subtitle = models.CharField(max_length=250)
    rehearsal_location = models.CharField(max_length=250)
    rehearsal_location_parking = models.CharField(max_length=250, blank=True)
    rehearsal_calendar = models.DateTimeField(unique=True, null=True)
    additional_rehearsal_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.rehearsal_calendar} {self.rehearsal_subtitle} {self.rehearsal_location}"

    def formatted_rehearsal_date(self):
        return self.rehearsal_calendar

    def formatted_rehearsal_location(self):
        return f"{self.rehearsal_location},{self.rehearsal_location_parking}"

    #def formatted_rehearsal_subtitle(self):
    #    return f"{self.rehearsal_subtitle}"





class CurrentRehearsal(models.Model):
    class Attendance(models.TextChoices):
        Present = "present", "present"
        Absent = "absent", "absent"
        Late = "late", "late"

    rehearsal = models.ForeignKey(RehearsalDate, on_delete=models.CASCADE, related_name='current_rehearsals', default=1)  # Default to the default_rehearsal
    attendance = models.IntegerField(choices=Attendance.choices)
    song = models.ForeignKey(Song, on_delete=models.PROTECT, related_name='current_rehearsals')
    attendee = models.ForeignKey(Attendee, on_delete=models.PROTECT, related_name='current_rehearsals')

    def save(self):
        if not self.rehearsal_id:
            default_rehearsal = RehearsalDate.objects.create(
                rehearsal_subtitle = "DefaultRehearsal",
                rehearsal_location = "Usual Location",
                rehearsal_location_parking = "",
                rehearsal_calendar = timezone.now(),
                additional_rehearsal_notes = "This is the default rehearsal"
            )
            self.rehearsal = default_rehearsal
        super().save()

    def __str__(self):
        return f"{self.rehearsal} {self.attendee} {self.get_attendance_display()}"
