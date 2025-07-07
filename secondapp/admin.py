from django.contrib import admin
from django.utils import timezone

# Register your models here.

from .models import Attendee
from .models import Song
from .models import CurrentRehearsal
from .models import RehearsalDate
from .models import AttendanceRecord

# classes
class AttendeeAdmin(admin.ModelAdmin):
    model = Attendee
    fieldsets = [
        ("Basic info", {"fields": ["first_name"]}),
        (None, {"fields": ["last_name"]}),
        (None, {"fields": ["instrument"]}),
        (None, {"fields": ["is_active"]}),
        (None, {"fields": ["skill_level"]}),
        ("Bio", {"fields": ["phone_number"]}),
        (None, {"fields":["email"]}),
        (None, {"fields": ["address"]}),
        (None, {"fields": ["date_of_birth"]}),
        (None, {"fields": ["messenger"]}),
        ("Other", {"fields": ["shirt_size"]}),
        (None, {"fields": ["date_of_joining"]}),
        (None, {"fields": ["additional_attendee_notes"]})
    ]
    #pass

class AttendanceRecordAdmin(admin.ModelAdmin):
    #list_display = ("date_record", "get_attendees", "attendance")   # (—> temporary out)     # bug hunting
    #list_filter = ("attendance",)
    #search_fields = ("attendees__first_name", "attendees__last_name")
    #filter_vertical = ("attendees",)

    def get_attendees(self, obj):
        return ", ".join([a.first_name for a in obj.attendees.all()])
    get_attendees.short_description = "Attendees"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(attendees__is_active=True)

    pass


class SongAdmin(admin.ModelAdmin):

    pass

class RehearsalDateAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["rehearsal_calendar"]}),
        (None, {"fields": ["rehearsal_subtitle"]}),
        ("Location", {"fields": ["rehearsal_location"]}),
        (None, {"fields": ["rehearsal_location_parking"]}),
    ]
    pass

    #def save_model(self, request, obj, form, change):
    #    timezone.activate(timezone.get_current_timezone())
    #    super().save_model(request, obj, form, change)


    #pass

class CurrentRehearsalAdmin(admin.ModelAdmin):
    #list_display = ("rehearsal", "song",) #"attendee", "attendance"
    #list_editable = ("attendance",)
    #list_filter = ("rehearsal", "song",) #"attendee", "attendance",
    #search_fields = ("rehearsal__rehearsal_subtitle", "song__song_title", "attendee__first_name", "attendee__last_name",),

    #fieldsets = [
    #    (None, {"fields": ["rehearsal_subtitle"]}),
    #    ("Date information", {"fields": ["date_of_rehearsal"], "classes": ["collapse"]}),
    #    ("Presence:", {"fields": ["attendee"]}),
    #    ("List of songs:", {"fields": ["song"]}),
    #]
    #inlines = [AttendeeAdmin]
    pass





admin.site.register(Attendee, AttendeeAdmin)
admin.site.register(AttendanceRecord, AttendanceRecordAdmin)
#admin.site.register(AttendanceDetail, AttendanceDetailAdmin)    # —> experimentation, currently out
admin.site.register(Song, SongAdmin)
admin.site.register(CurrentRehearsal, CurrentRehearsalAdmin)
admin.site.register(RehearsalDate, RehearsalDateAdmin)


