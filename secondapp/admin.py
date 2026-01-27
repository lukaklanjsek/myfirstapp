from django.contrib import admin
from django.utils import timezone
from import_export.admin import ImportExportModelAdmin

# Register your models here.

# from .models import Tag
# from .models import Song
# from .models import Rehearsal
# from .models import Member, Composer, Arranger, Poet, Musician, Conductor, Ensemble, Activity
from django.contrib.auth.admin import UserAdmin
from .models import AuthUser

class CustomUserAdmin(UserAdmin):
    model = AuthUser
    list_display = ['email', 'first_name', 'last_name', 'is_staff']
    search_fields = ['email']

admin.site.register(AuthUser, CustomUserAdmin)

# classes

# class SongInline(admin.StackedInline):
#     model = Song
#     pass
#
# class ActivityInLine(admin.StackedInline):
#     model = Activity
#     pass
#
# class EnsembleAdmin(admin.ModelAdmin):
#     model = Ensemble
#     pass
#
# class TagAdmin(ImportExportModelAdmin):
#     pass
#
# class MemberAdmin(ImportExportModelAdmin):
#     model = Member
#     inlines = [ActivityInLine]
#     pass
#
# class ComposerAdmin(ImportExportModelAdmin):
#     pass
#
# class ArrangerAdmin(ImportExportModelAdmin):
#     pass
#
# class PoetAdmin(ImportExportModelAdmin):
#     pass
#
# class MusicianAdmin(ImportExportModelAdmin):
#     pass
#
# class ConductorAdmin(ImportExportModelAdmin):
#     inlines = [ActivityInLine]
#     pass
#
# class RehearsalAdmin(ImportExportModelAdmin):
#     model = Rehearsal
#     filter_horizontal = ["songs", "members"]
#     pass
#
# class SongAdmin(ImportExportModelAdmin):
#     pass







# admin.site.register(Tag, TagAdmin)
# admin.site.register(Ensemble, EnsembleAdmin)
# admin.site.register(Song)#, SongAdmin)
# admin.site.register(Rehearsal, RehearsalAdmin)
# admin.site.register(Member, MemberAdmin)
# admin.site.register(Composer, ComposerAdmin)
# admin.site.register(Arranger, ArrangerAdmin)
# admin.site.register(Poet, PoetAdmin)
# admin.site.register(Musician, MusicianAdmin)
# admin.site.register(Conductor, ConductorAdmin)
