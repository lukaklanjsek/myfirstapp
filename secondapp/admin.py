from django.contrib import admin

# Register your models here.

from .models import Attendee
from .models import Song
from .models import CurrentRehearsal

admin.site.register(Attendee)
admin.site.register(Song)
admin.site.register(CurrentRehearsal)


