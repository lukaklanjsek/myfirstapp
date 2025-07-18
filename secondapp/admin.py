from django.contrib import admin
from django.utils import timezone

# Register your models here.

from .models import Tag
from .models import Song
from .models import Rehearsal
from .models import Singer, Composer, Arranger, Poet, Musician

# classes

class TagAdmin(admin.ModelAdmin):
    pass

class SingerAdmin(admin.ModelAdmin):
    pass

class ComposerAdmin(admin.ModelAdmin):
    pass

class ArrangerAdmin(admin.ModelAdmin):
    pass

class PoetAdmin(admin.ModelAdmin):
    pass

class MusicianAdmin(admin.ModelAdmin):
    pass




class SongInline(admin.StackedInline):
    model = Song
    pass


class RehearsalAdmin(admin.ModelAdmin):
    model = Rehearsal
    filter_horizontal = ["songs", "singers", "tags"]
    pass



admin.site.register(Tag)

admin.site.register(Song)#, SongAdmin)
admin.site.register(Rehearsal, RehearsalAdmin)
admin.site.register(Singer, SingerAdmin)
admin.site.register(Composer, ComposerAdmin)
admin.site.register(Arranger, ArrangerAdmin)
admin.site.register(Poet, PoetAdmin)
admin.site.register(Musician, MusicianAdmin)

