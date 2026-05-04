from django import forms
import datetime
# from .models import Song, Person, Member, Composer, Musician, Arranger, Poet, Tag
# from .models import Rehearsal, Activity, Conductor, Ensemble, ImportFile
# from django_select2.forms import ModelSelect2MultipleWidget
#It is advised to always setup a separate cache server for Select2.
# from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, Organization, Person, Song, Skill, Role, Quote, Project
from .models import Event, EventSong, Attendance, AttendanceType, Singer, Voice, Instrument, EventType
from .models import LyricsTranslation, LanguageCode, ApproximateDate
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.db.models import Q
from django.utils import timezone

# class SongWidget(ModelSelect2MultipleWidget):
#     model = Song
#     search_fields = [
#         "title__icontains",
#         "composer__first_name__icontains",
#         "composer__last_name__icontains",
#         "poet__first_name__icontains",
#         "poet__last_name__icontains"
#     ]


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("email", "username",)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ("email",)


class RegisterForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = "__all__"


class PersonForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = Person
        fields = [
            "first_name",
            "last_name",
            "email",
            "address",
            "phone",
            "birth_date",
        ]
        widgets = {
            "birth_date": forms.SelectDateWidget(
                years=range(datetime.date.today().year, 1930, -1)
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            # editing current user
            self.fields["email"].initial = self.instance.email
        elif user and user.is_authenticated:
            # new user - grab email from user
            self.fields["email"].initial = user.email

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ["name", "email", "address"]


class OrgMemberForm(forms.Form):  # Person + Membership + MembershipPeriod
    VALID_PRESETS = {'composer', 'poet', 'translator'}
    # Person
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=23, required=False)
    address = forms.CharField(required=False, widget=forms.Textarea)
    # Date fields
    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    birth_approximate = forms.ModelChoiceField(
        queryset=ApproximateDate.objects.all(),
        required=False,
        empty_label="Exact date",
        label="Birth date approximation"
    )
    death_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    death_approximate = forms.ModelChoiceField(
        queryset=ApproximateDate.objects.all(),
        required=False,
        empty_label="Exact date",
        label="Death date approximation"
    )
    # Role checkboxes
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all(),
        required=True,
        widget=forms.CheckboxSelectMultiple
    )
    # Skill checkbox
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    # Voice select multiple
    voices = forms.ModelMultipleChoiceField(
        queryset=Voice.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'size': '6',  # Shows 6 options at once
            # 'class': 'form-select'  # Optional: for styling
        }),
        label='Voice Types'
    )
    # Instrument select multiple
    instruments = forms.ModelMultipleChoiceField(
        queryset=Instrument.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'size': '6',  # Shows 6 options at once
            # 'class': 'form-select'  # Optional: for styling
        }),
        label='Instrument Types'
    )

    def __init__(self, *args, preset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if preset not in self.VALID_PRESETS:
            preset = None

        # Apply presets
        if preset == 'composer':
            external_role = Role.objects.filter(title__iexact='external').first()
            composer_skill = Skill.objects.filter(title__iexact="composer").first()
            if external_role and composer_skill:
                self.initial['roles'] = [external_role.id]
                self.initial["skills"] = [composer_skill.id]

        elif preset == 'poet':
            poet_skill = Skill.objects.filter(title__iexact="poet").first()
            external_role = Role.objects.filter(title__iexact="external").first()
            if poet_skill and external_role:
                self.initial['roles'] = [external_role.id]
                self.initial["skills"] = [poet_skill.id]

        elif preset == 'translator':
            translator_skill = Skill.objects.filter(title__iexact="translator").first()
            external_role = Role.objects.filter(title__iexact="external").first()
            if translator_skill and external_role:
                self.initial['roles'] = [external_role.id]
                self.initial["skills"] = [translator_skill.id]

        # For edit mode: pre-populate voice
        # if person:
        #     self.initial['voices'] = Voice.objects.filter(
        #         singer__person=person
        #     )


class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ['word', 'bar_number']
        labels = {
            'word': 'Quote',
            'bar_number': 'Bar Number',
        }
        widgets = {
            'word': forms.TextInput(attrs={'placeholder': 'Quote text'}),
            'bar_number': forms.TextInput(attrs={'placeholder': '43'}),
        }


class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = [
            "internal_id",
            "title",
            "composer",
            "poet",
            "translator",
            "number_of_pages",
            "number_of_copies",
            "year",
            "group",
            "number_of_voices",
            "additional_notes",
            "lyrics",
            "languagecode",
            "keywords",
        ]
        widgets = {
            "lyrics": forms.Textarea(attrs={'rows': 12}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user:
            self.fields['composer'].queryset = Person.objects.for_user_with_skill(user=user, skill_id=Skill.COMPOSER)
            self.fields['poet'].queryset = Person.objects.for_user_with_skill(user=user, skill_id=Skill.POET)
            self.fields['translator'].queryset = Person.objects.for_user_with_skill(user=user, skill_id=Skill.TRANSLATOR)


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'title',
            'description',
            'start_date',
            'end_date',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ["title", "additional_notes"]


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name',
                  'location',
                  'description',
                  'started_at',
                  'ended_at',
                  'event_type',
                  'details',
                  'project',
                  'producers',
                  'additional_notes',
                  'num_visitors',
                  ]
        widgets = {
            'started_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'ended_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'location': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Order projects by start date (most recent first)
        qs = Project.objects.all() if user is None else Project.objects.filter(user=user)
        self.fields['project'].queryset = qs.order_by('-start_date').distinct()

        # Pre-select "rehearsal" event type and remove empty option
        rehearsal_event_type = EventType.objects.get(pk=EventType.REHEARSAL)
        self.fields['event_type'].initial = rehearsal_event_type
        self.fields['event_type'].empty_label = None


class EventSongForm(forms.ModelForm):
    class Meta:
        model = EventSong
        fields = ['id', 'song', 'encore']
        widgets = {
            'id': forms.HiddenInput(),
            'song': forms.HiddenInput(),
            'encore': forms.CheckboxInput(),
        }


class EventSongFormSet(BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            for form in self.forms:
                form.errors.pop('__all__', None)


class SongChoiceField(forms.ModelChoiceField):
    def __init__(self, *args, already_added_ids=None, **kwargs):
        self.already_added_ids = already_added_ids or set()
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        label = str(obj)
        if obj.pk in self.already_added_ids:
            return f"* {label}"
        return label


class AddSongToEventForm(forms.Form):
    encore = forms.BooleanField(required=False, label='Encore')

    def __init__(self, *args, org_user=None, event=None, search_q='', **kwargs):
        super().__init__(*args, **kwargs)
        if org_user and event is not None:
            already_added_ids = set(event.eventsong_set.values_list('song_id', flat=True))
            qs = Song.objects.filter(user=org_user).order_by('title')
            if search_q:
                if search_q.isdigit():
                    qs = qs.filter(internal_id=int(search_q))
                else:
                    qs = qs.filter(
                        Q(title__icontains=search_q) |
                        Q(composer__last_name__icontains=search_q) |
                        Q(keywords__icontains=search_q)
                    ).distinct()
            self.fields['song'] = SongChoiceField(
                queryset=qs,
                already_added_ids=already_added_ids,
                widget=forms.Select(attrs={'size': '8'}),
                empty_label=None,
                label='Song',
            )


class EventChoiceField(forms.ModelChoiceField):
    def __init__(self, *args, already_added_ids=None, other_project_ids=None, **kwargs):
        self.already_added_ids = already_added_ids or set()
        self.other_project_ids = other_project_ids or {}
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        # Format: "Event Name (2024-12-25 19:00 - 21:00)"
        label = f"{obj.name} ({obj.started_at.strftime('%Y-%m-%d %H:%M')} - {obj.ended_at.strftime('%H:%M')})"
        if obj.pk in self.already_added_ids:
            return f"* {label}"
        if obj.pk in self.other_project_ids:
            other_project = self.other_project_ids[obj.pk]
            return f"⚠ {label} (in: {other_project})"
        return label


class AddEventToProjectForm(forms.Form):
    def __init__(self, *args, org_user=None, project=None, search_q='', **kwargs):
        super().__init__(*args, **kwargs)
        if org_user and project is not None:
            already_added_ids = set(project.events.values_list('id', flat=True))
            qs = Event.objects.filter(user=org_user).order_by('-started_at')
            if search_q:
                qs = qs.filter(name__icontains=search_q)

            # Build a mapping of events in other projects
            other_project_ids = {}
            for event in qs.exclude(project__isnull=True):
                other_project_ids[event.pk] = event.project.title

            self.fields['event'] = EventChoiceField(
                queryset=qs,
                already_added_ids=already_added_ids,
                other_project_ids=other_project_ids,
                widget=forms.Select(attrs={'size': '8'}),
                empty_label=None,
                label='Event',
            )


class AddSongToProjectForm(forms.Form):
    def __init__(self, *args, org_user=None, project=None, search_q='', **kwargs):
        super().__init__(*args, **kwargs)
        if org_user and project is not None:
            already_added_ids = set(project.songs.values_list('id', flat=True))
            qs = Song.objects.filter(user=org_user).order_by('title')
            if search_q:
                if search_q.isdigit():
                    qs = qs.filter(internal_id=int(search_q))
                else:
                    qs = qs.filter(
                        Q(title__icontains=search_q) |
                        Q(composer__last_name__icontains=search_q) |
                        Q(keywords__icontains=search_q)
                    ).distinct()
            self.fields['song'] = SongChoiceField(
                queryset=qs,
                already_added_ids=already_added_ids,
                widget=forms.Select(attrs={'size': '8'}),
                empty_label=None,
                label='Song',
            )


class AddGuestToProjectForm(forms.Form):
    def __init__(self, *args, org_user=None, project=None, search_q='', **kwargs):
        super().__init__(*args, **kwargs)
        if org_user and project is not None:
            already_added_ids = set(project.guests.values_list('id', flat=True))
            qs = Person.objects.filter(
                membership_period__user=org_user,
            ).distinct()
            if search_q:
                qs = qs.filter(
                    Q(first_name__icontains=search_q) |
                    Q(last_name__icontains=search_q)
                ).distinct()
            qs = qs.order_by('last_name', 'first_name')
            self.fields['guest'] = forms.ModelChoiceField(
                queryset=qs,
                widget=forms.Select(attrs={'size': '8'}),
                empty_label=None,
                label='Guest',
            )


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['id', 'person', 'attendance_type']
        widgets = {
            'id': forms.HiddenInput(),
            'person': forms.HiddenInput(),
            'attendance_type': forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        person_queryset = kwargs.pop('person_queryset', None)
        kwargs.pop('user', None)
        kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        if person_queryset is not None:
            if self.instance and self.instance.person_id:
                self.fields['person'].queryset = Person.objects.filter(
                    Q(pk__in=person_queryset) | Q(pk=self.instance.person_id)
                )
            else:
                self.fields['person'].queryset = person_queryset



class AddAttendanceForm(forms.Form):
    """Admin-only form to add any org person to an event's attendance."""
    person = forms.ModelChoiceField(
        queryset=Person.objects.none(),
        widget=forms.Select(attrs={'size': '8'}),
        empty_label=None,
        label='Person',
    )
    attendance_type = forms.ModelChoiceField(
        queryset=AttendanceType.objects.all(),
        widget=forms.RadioSelect(),
        label='Attendance Type',
    )

    def __init__(self, *args, org_user=None, event=None, search_q='', **kwargs):
        super().__init__(*args, **kwargs)
        if org_user and event:
            from django.db.models import Exists, OuterRef, ExpressionWrapper, BooleanField
            from .models import Singer, Instrumentalist
            already_attending = event.attendance_set.values_list('person_id', flat=True)
            qs = Person.objects.filter(
                membership_period__user=org_user,
            ).exclude(
                id__in=already_attending
            ).distinct()
            if search_q:
                qs = qs.filter(
                    Q(first_name__icontains=search_q) |
                    Q(last_name__icontains=search_q) |
                    Q(singer__voice__name__icontains=search_q) |
                    Q(instrumentalist__instrument__name__icontains=search_q)
                ).distinct()
            qs = qs.annotate(
                is_performer=ExpressionWrapper(
                    Exists(Singer.objects.filter(person=OuterRef('pk'))) |
                    Exists(Instrumentalist.objects.filter(person=OuterRef('pk'))),
                    output_field=BooleanField()
                )
            ).order_by('-is_performer', 'last_name', 'first_name')
            self.fields['person'].queryset = qs


# Formset factories  ------------------------------------------------------
EventSongFormSet = inlineformset_factory(
    Event,
    EventSong,
    form=EventSongForm,
    formset=EventSongFormSet,
    extra=0,
    can_delete=True,
)

AttendanceFormSet = inlineformset_factory(
    Event,
    Attendance,
    form=AttendanceForm,
    extra=0,
    can_delete=True,
)

QuoteFormSet = inlineformset_factory(
    Song,
    Quote,
    form=QuoteForm,
    extra=1,
    can_delete=True,
)


class LyricsTranslationForm(forms.ModelForm):
    class Meta:
        model = LyricsTranslation
        fields = ['languagecode', 'translation', 'translator']
        widgets = {'translation': forms.Textarea(attrs={'rows': 5})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['languagecode'].queryset = LanguageCode.objects.all()
        if user:
            self.fields['translator'].queryset = Person.objects.for_user_with_skill(
                user=user, skill_id=Skill.TRANSLATOR
            )
        else:
            self.fields['translator'].queryset = Person.objects.none()


class BaseLyricsTranslationFormSet(BaseInlineFormSet):
    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['user'] = self.user
        return kwargs


LyricsTranslationFormSet = inlineformset_factory(
    Song,
    LyricsTranslation,
    form=LyricsTranslationForm,
    formset=BaseLyricsTranslationFormSet,
    extra=1,
    can_delete=True,
)
# initial = []
# if 'members' in context:
#     for member in context['members']:
#         initial.append({'person': member.id})
# formset = AttendanceFormSet(instance=event, initial=initial)
######################################
# class SingerForm(forms.Form):
#     options = forms.MultipleChoiceField(
#         required=False,
#         widget=forms.CheckboxSelectMultiple,
#     )
#
#     def __init__(self, choices=None, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         if choices:
#             self.fields['options'].choices = choices
#
# class InstrumentalistForm(forms.Form):
#     options = forms.MultipleChoiceField(
#         required=False,
#         widget=forms.CheckboxSelectMultiple,
#     )
#
#     def __init__(self, choices=None, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         if choices:
#             self.fields['options'].choices = choices



##########################################################################
# class BaseForm(forms.ModelForm):
#     # required field indicator
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         for field_name, field in self.fields.items():
#             if field.required:
#                 field.label = f"{field.label} *"
#             else:
#                 field.label = f"{field.label}"
#
#
# class PersonForm(BaseForm):
#     class Meta:
#         model = Person
#         fields = [
#             "first_name",
#             "last_name",
#             "address",
#             "email",
#             "phone_number",
#             "mobile_number",
#             "birth_date",
#             "additional_notes"
#         ]
#
#
#
# class MemberForm(PersonForm):
#     class Meta:
#         model = Member
#         fields = PersonForm.Meta.fields + [
#             "voice",
#             "is_active",
#             "date_active"
#         ]
#         widgets = {
#             "birth_date": forms.SelectDateWidget(),
#         }
#
#
# class ComposerForm(PersonForm):
#     class Meta:
#         model = Composer
#         fields = PersonForm.Meta.fields + ["musical_era"]
#         widgets = {
#             "birth_date": forms.SelectDateWidget(),
#         }
#
#
# class PoetForm(PersonForm):
#     class Meta:
#         model = Poet
#         fields = PersonForm.Meta.fields + ["writing_style", "literary_style"]
#         widgets = {
#             "birth_date": forms.SelectDateWidget(),
#         }
#
#
# class ArrangerForm(PersonForm):
#     class Meta:
#         model = Arranger
#         fields = PersonForm.Meta.fields + ["style"]
#         widgets = {
#             "birth_date": forms.SelectDateWidget(),
#         }
#
#
# class MusicianForm(PersonForm):
#     class Meta:
#         model = Musician
#         fields = PersonForm.Meta.fields + ["instrument"]
#         widgets = {
#             "birth_date": forms.SelectDateWidget(),
#         }
#
# class ConductorForm(PersonForm):
#     class Meta:
#         model = Conductor
#         fields = PersonForm.Meta.fields + [
#             "is_active",
#             "date_joined"
#         ]
#         widgets = {
#                 "birth_date": forms.SelectDateWidget(),
#             }
#
#
# class SongForm(BaseForm):
#     class Meta:
#         model = Song
#         fields = "__all__"
#
#
#
# class RehearsalForm(BaseForm):
#     class Meta:
#         model = Rehearsal
#         fields = ["calendar",
#                   "additional_notes",
#                   "songs",
#                   "is_canceled"]
#         widgets = {
#             'calendar': forms.DateTimeInput(
#                 attrs={"type": "datetime-local"}
#             ),
#             'additional_notes': forms.Textarea(attrs={'rows': 3}),
#             'songs': SongWidget(attrs={'style': 'width: 100%;'}),
#         }
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['songs'].required = False
#         self.fields['is_canceled'].label = "Mark as cancelled"
#
#         self.active_members = Member.objects.filter(is_active=True).order_by('last_name', 'first_name')
#         self.active_conductors = Conductor.objects.filter(is_active=True).order_by('last_name', 'first_name')
#         self._create_person_fields()
#
#         if instance := kwargs.get("instance"):
#             self._set_initial_values(instance)
#
#     def _create_person_fields(self):
#         # making space for conductors as well as members
#         for member in self.active_members:
#             field_name = f'member_{member.id}'
#             self.fields[field_name] = forms.BooleanField(
#                 required=False,
#                 initial=True,
#                 label=f"{member.first_name} {member.last_name}"
#             )
#         for conductor in self.active_conductors:
#             field_name = f'conductor_{conductor.id}'
#             self.fields[field_name] = forms.BooleanField(
#                 required=False,
#                 initial=True,
#                 label=f"{conductor.first_name} {conductor.last_name} (Conductor)"
#             )
#
#     def _set_initial_values(self, instance):
#         # Set checkbox initial values based on pre-save
#         current_members = instance.members.all()
#         for member in self.active_members:
#             field_name = f"member_{member.id}"
#             if field_name in self.fields:
#                 self.fields[field_name].initial = member in current_members
#
#         current_conductors = instance.conductors.all()
#         for conductor in self.active_conductors:
#             field_name = f"conductor_{conductor.id}"
#             if field_name in self.fields:
#                 self.fields[field_name].initial = conductor in current_conductors
#
#
#     def save(self, *args, **kwargs):
#         instance = super().save(*args, **kwargs)
#
#         #clean and update
#         instance.members.clear()
#         selected_member_ids = [
#             member.id for member in self.active_members
#             if self.cleaned_data.get(f'member_{member.id}', False)
#         ]
#         if selected_member_ids:
#             instance.members.add(*selected_member_ids)
#
#         #clean and update
#         instance.conductors.clear()
#         selected_conductor_ids = [
#             conductor.id for conductor in self.active_conductors
#             if self.cleaned_data.get(f'conductor_{conductor.id}', False)
#         ]
#         if selected_conductor_ids:
#             instance.conductors.add(*selected_conductor_ids)
#
#         return instance
#
#
# class TagForm(forms.ModelForm):
#     class Meta:
#         model = Tag
#         fields = ["name"]
#
#
# class EnsembleForm(BaseForm):
#     class Meta:
#         model = Ensemble
#         fields = ["name", "address", "additional_notes"]
#
# class ActivityForm(BaseForm):
#     class Meta:
#         model = Activity
#         fields = [
#             "start_date",
#             "end_date",
#             "ensemble"
#         ]
#         widgets = {
#             "start_date": forms.SelectDateWidget(),
#             "end_date": forms.SelectDateWidget(),
#         }
#
# class ImportFileForm(BaseForm):
#     file = forms.FileField()
#     import_mode = forms.ChoiceField(choices=[("songs", "Songs",), ("members", "Members",)], required=True)
#     class Meta:
#         model = ImportFile
#         fields = [
#             "title",
#             "file"
#         ]
