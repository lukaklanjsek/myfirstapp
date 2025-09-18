from django import forms
from .models import Song, Person, Singer, Composer, Musician, Arranger, Poet, Tag
from .models import Rehearsal, Activity, Conductor, Ensemble
from django_flatpickr.widgets import DateTimePickerInput
from formset.widgets import DualSelector


class BaseForm(forms.ModelForm):
    # required field indicator
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if field.required:
                field.label = f"{field.label} *"
            else:
                field.label = f"{field.label}"


class PersonForm(BaseForm):
    class Meta:
        model = Person
        fields = [
            "first_name",
            "last_name",
            "third_name",
            "phone_number",
            "email",
            "address",
            "birth_date",
            "death_date",
            "nationality",
            "biography",
            "favorite_works",
            "influenced_by",
            "awards",
            "website",
            #"tags",
            "additional_notes"
        ]


#    def __init__(self, *args, **kwargs):
#        super().__init__(*args, **kwargs)

#        for field_name, field in self.fields.items():
#            if field.required:
#                field.label = f"{field.label} *"
#            else:
#                field.label = f"{field.label} (-)"


class SingerForm(PersonForm):
    class Meta:
        model = Singer
        fields = PersonForm.Meta.fields + [
            "voice",
            "is_active",
            "skill_level",
            "messenger",
            "shirt_size",
            "date_joined"
        ]
        widgets = {"date_joined": DateTimePickerInput(attrs={'class': 'datepicker'}),
                   "birth_date": DateTimePickerInput(attrs={'class': 'datepicker'}),
                   "death_date": DateTimePickerInput(attrs={'class': 'datepicker'}),
        }


class ComposerForm(PersonForm):
    class Meta:
        model = Composer
        fields = PersonForm.Meta.fields + ["work_style", "musical_era", "instruments"]
        widgets = {
            "birth_date": DateTimePickerInput(attrs={'class': 'datepicker'}),
            "death_date": DateTimePickerInput(attrs={'class': 'datepicker'}),
        }


class PoetForm(PersonForm):
    class Meta:
        model = Poet
        fields = PersonForm.Meta.fields + ["writing_style", "literary_style"]
        widgets = {
            "birth_date": DateTimePickerInput(attrs={'class': 'datepicker'}),
            "death_date": DateTimePickerInput(attrs={'class': 'datepicker'}),
        }


class ArrangerForm(PersonForm):
    class Meta:
        model = Arranger
        fields = PersonForm.Meta.fields + ["style", "instruments"]
        widgets = {
            "birth_date": DateTimePickerInput(attrs={'class': 'datepicker'}),
            "death_date": DateTimePickerInput(attrs={'class': 'datepicker'}),
        }


class MusicianForm(PersonForm):
    class Meta:
        model = Musician
        fields = PersonForm.Meta.fields + ["instrument", "genre"]
        widgets = {
            "birth_date": DateTimePickerInput(attrs={'class': 'datepicker'}),
            "death_date": DateTimePickerInput(attrs={'class': 'datepicker'}),
        }

class ConductorForm(PersonForm):
    class Meta:
        model = Conductor
        fields = PersonForm.Meta.fields + [
            "is_active",
            "messenger",
            "date_joined"
        ]
        widgets = {
            "date_joined": DateTimePickerInput(attrs={'class': 'datepicker'}),
            "birth_date": DateTimePickerInput(attrs={'class': 'datepicker'}),
            "death_date": DateTimePickerInput(attrs={'class': 'datepicker'}),
        }


class SongForm(BaseForm):
    class Meta:
        model = Song
        fields = "__all__"


class RehearsalForm(BaseForm):
    class Meta:
        model = Rehearsal
        fields = ["subtitle","location", "parking", "calendar", "additional_notes",
                  "singers", "conductors", "songs", "tags", "duration_minutes", "attendance_count",
                  "is_cancelled"]
        widgets = {
            'calendar': DateTimePickerInput(attrs={'class': 'datetimepicker'}),
            'duration_minutes': forms.NumberInput(attrs={'min': '1', 'placeholder': 'e.g. 180'}),
            'additional_notes': forms.Textarea(attrs={'rows': 3}),
            'singers': DualSelector(search_lookup='first_name'),
            'conductors': DualSelector(search_lookup='first_name'),
            'songs': DualSelector(search_lookup='title'),
            'tags': DualSelector(search_lookup='name'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['singers'].queryset = Singer.objects.filter(is_active=True)
        self.fields['songs'].required = False
        self.fields['is_cancelled'].label = "Mark as cancelled"
        self.fields['duration_minutes'].label = "Expected duration (minutes) *"
        self.fields['attendance_count'].label = "Actual attendance count"


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name"]


class EnsembleForm(BaseForm):
    class Meta:
        model = Ensemble
        fields = ["name", "address", "additional_notes"]

class ActivityForm(BaseForm):
    class Meta:
        model = Activity
        fields = [
            "start_date",
            "end_date",
            "ensemble"
        ]
        widgets = {
            "start_date": DateTimePickerInput(attrs={'class': 'datepicker'}),
            "end_date": DateTimePickerInput(attrs={'class': 'datepicker'}),
        }