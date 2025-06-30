from django.contrib import admin

# Register your models here.

from .models import Attendee
from .models import Song
from .models import CurrentRehearsal
from .models import RehearsalDates

# classes
class AttendeeAdmin(admin.ModelAdmin):
    pass

class SongAdmin(admin.ModelAdmin):
    pass

class RehearsalDatesAdmin(admin.ModelAdmin):
    pass

class CurrentRehearsalAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["rehearsal_subtitle"]}),
        ("Date information", {"fields": ["date_of_rehearsal"], "classes": ["collapse"]}),
        ("Presence:", {"fields": ["attendee"]}),
        ("List of songs:", {"fields": ["song"]}),
    ]





admin.site.register(Attendee, AttendeeAdmin)
admin.site.register(Song, SongAdmin)
admin.site.register(CurrentRehearsal, CurrentRehearsalAdmin)
admin.site.register(RehearsalDates, RehearsalDatesAdmin)


