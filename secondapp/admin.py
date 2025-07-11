from django.contrib import admin
from django.utils import timezone

# Register your models here.

from .models import Member
from .models import Song
from .models import Rehearsal

# classes

class MemberInline(admin.StackedInline):
    model = Member
    pass


class SongInline(admin.StackedInline):
    model = Song
    pass


class RehearsalAdmin(admin.ModelAdmin):
    model = Rehearsal
    filter_horizontal = ["songs", "members"]
    pass



admin.site.register(Member)#, MemberAdmin)
admin.site.register(Song)#, SongAdmin)
admin.site.register(Rehearsal, RehearsalAdmin)


