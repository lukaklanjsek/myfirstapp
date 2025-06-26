from django.db import models


# Create your models here.



class Attendee(models.Model):
    # choices within class attributes:
    SHIRT_SIZES = [
        ('XXS', '2x Extra Small'),
        ('XS', 'Extra Small'),
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', '2x Extra Large'),
        ('XXXL', '3x Extra Large'),
    ]

    VOICE_TYPES = [
        ('S1', 'Soprano'),
        ('MS', 'Mezzo-Soprano'),
        ('A1', 'Higher-Alto'),
        ('A2', 'Lower-Alto'),
        ('CA', 'Contra-Alto'),
        ('CT', 'Counter-Tenor'),
        ('T1', 'Higher-Tenor'),
        ('T2', 'Lower-Tenor'),
        ('B1', 'Baritone'),
        ('B2', 'Bass'),
        ('CB', 'Contra-Bass'),
    ]

    SKILL_LEVEL = [
        ("1", "Beginner"),
        ("2", "Enthusiast"),
        ("3", "Experienced"),
        ("4", "Schooled"),
        ("5", "Professional"),
    ]



    # model fields:
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    instrument = models.CharField(max_length=2, choices=VOICE_TYPES)
    is_active = models.BooleanField(default=True)
    expert_level = models.CharField(max_length=1, choices=SKILL_LEVEL)
    phone_number = models.CharField(max_length=17, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=250, blank=True)
    date_of_birth = models.DateField("birthday")
    messenger = models.CharField(max_length=250, blank=True)
    #photo =    ->    # to be added later (I need to rethink)
    shirt_size = models.CharField(max_length=4, choices=SHIRT_SIZES)
    additional_attendee_notes = models.TextField()

class Songs(models.Model):
    # choices within Songs class:
    DIFFICULTY_LEVEL = [
        ("1", "Beginner"),
        ("2", "Enthusiast"),
        ("3", "Experienced"),
        ("4", "Schooled"),
        ("5", "Professional"),
    ]

    # model fields:
    title =  models.CharField(max_length=250)
    composer =  models.CharField(max_length=250)
    author = models.CharField(max_length=250)
    genre =  models.CharField(max_length=250)
    number_of_copies = models.CharField(max_length=4)
    number_of_pages = models.CharField(max_length=4)
    number_of_voices = models.CharField(max_length=4)
    difficulty_level =  models.CharField(max_length=1, choices=DIFFICULTY_LEVEL)
    transcript = models.TextField()
    translation = models.TextField()
    speech_articulation = models.TextField()
    # date_of_rehearsal = models.DateField("date of rehearsal")
    date_of_concert = models.DateField("date of concert")
    additional_songs_notes = models.TextField()


class RehearsalDates(models.Model):
    rehearsal_subtitle = models.CharField(max_length=250)
    rehearsal_location = models.CharField(max_length=250)
    rehearsal_calendar_specific = models.DateField("rehearsal specific date")
    additional_rehearsal_notes = models.TextField()





class CurrentRehearsal(models.Model):
    class Attendance(models.IntegerChoices):
        Present = 1, "present"
        Absent = 2, "absent"
        Late = 3, "late"

    date_of_rehearsal = models.ForeignKey(RehearsalDates, on_delete=models.CASCADE)
    attendance = models.IntegerField(choices=Attendance)
    songs = models.ForeignKey(Songs, on_delete=models.PROTECT)
    attendee = models.ForeignKey(Attendee, on_delete=models.PROTECT)


