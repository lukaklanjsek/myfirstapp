from django.contrib import admin

# Register your models here.

from .models import Attendee
from .models import Song
from .models import CurrentRehearsal
from .models import RehearsalDate

# classes
class AttendeeAdmin(admin.StackedInline):
    #model = Attendee
    #fields = ["first_name", "last_name", "instrument"]
    pass


class SongAdmin(admin.ModelAdmin):
    pass

class RehearsalDateAdmin(admin.ModelAdmin):
    pass

class CurrentRehearsalAdmin(admin.ModelAdmin):
    #list_display = [""]
    #fieldsets = [
    #    (None, {"fields": ["rehearsal_subtitle"]}),
    #    ("Date information", {"fields": ["date_of_rehearsal"], "classes": ["collapse"]}),
    #    ("Presence:", {"fields": ["attendee"]}),
    #    ("List of songs:", {"fields": ["song"]}),
    #]
    #inlines = [AttendeeAdmin]
    pass





#admin.site.register(Attendee, AttendeeAdmin)
admin.site.register(Song, SongAdmin)
admin.site.register(CurrentRehearsal, CurrentRehearsalAdmin)
admin.site.register(RehearsalDate, RehearsalDateAdmin)


