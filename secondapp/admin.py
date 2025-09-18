from django.contrib import admin
from django.utils import timezone
from import_export.admin import ImportExportModelAdmin

# Register your models here.

from .models import Tag
from .models import Song
from .models import Rehearsal
from .models import Singer, Composer, Arranger, Poet, Musician, Conductor, Ensemble, Activity

# classes

class SongInline(admin.StackedInline):
    model = Song
    pass

class ActivityInLine(admin.StackedInline):
    model = Activity
    pass

class EnsembleAdmin(admin.ModelAdmin):
    model = Ensemble
    pass

class TagAdmin(ImportExportModelAdmin):
    pass

class SingerAdmin(ImportExportModelAdmin):
    model = Singer
    inlines = [ActivityInLine]
    pass

class ComposerAdmin(ImportExportModelAdmin):
    pass

class ArrangerAdmin(ImportExportModelAdmin):
    pass

class PoetAdmin(ImportExportModelAdmin):
    pass

class MusicianAdmin(ImportExportModelAdmin):
    pass

class ConductorAdmin(ImportExportModelAdmin):
    inlines = [ActivityInLine]
    pass

class RehearsalAdmin(ImportExportModelAdmin):
    model = Rehearsal
    filter_horizontal = ["songs", "singers", "tags"]
    pass

class SongAdmin(ImportExportModelAdmin):
    pass







admin.site.register(Tag, TagAdmin)
admin.site.register(Ensemble, EnsembleAdmin)
admin.site.register(Song)#, SongAdmin)
admin.site.register(Rehearsal, RehearsalAdmin)
admin.site.register(Singer, SingerAdmin)
admin.site.register(Composer, ComposerAdmin)
admin.site.register(Arranger, ArrangerAdmin)
admin.site.register(Poet, PoetAdmin)
admin.site.register(Musician, MusicianAdmin)
admin.site.register(Conductor, ConductorAdmin)
