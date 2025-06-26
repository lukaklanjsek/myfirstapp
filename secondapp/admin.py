from django.contrib import admin

# Register your models here.

from .models import Attendee
from .models import Songs
from .models import CurrentRehearsal

admin.site.register(Attendee)
admin.site.register(Songs)
admin.site.register(CurrentRehearsal)


