from django import forms
from .models import Song, Person, Singer, Composer, Musician, Arranger, Poet, Tag
from .models import Rehearsal, Activity, Conductor, Ensemble, ImportFile
#from .widgets import DateInput, DateTimeInput
from django_select2 import forms as s2forms
from django_select2.forms import ModelSelect2MultipleWidget
from django_flatpickr.widgets import DatePickerInput, DateTimePickerInput


class SingerWidget(ModelSelect2MultipleWidget):
    model = Singer
    search_fields = [
        "first_name__icontains",
        "last_name__icontains",
    ]

    def get_queryset(self):
        return Singer.objects.filter(is_active=True)

class SongWidget(ModelSelect2MultipleWidget):
    model = Song
    search_fields = [
        "title__icontains",
        "composer__icontains",
    ]


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
            "additional_notes"
        ]



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
        widgets = {"date_joined": DatePickerInput(),
                   "birth_date": DatePickerInput(),
                   "death_date": DatePickerInput(),
        }


class ComposerForm(PersonForm):
    class Meta:
        model = Composer
        fields = PersonForm.Meta.fields + ["musical_era"]
        widgets = {
            "birth_date": DatePickerInput(),
            "death_date": DatePickerInput(),
        }


class PoetForm(PersonForm):
    class Meta:
        model = Poet
        fields = PersonForm.Meta.fields + ["writing_style", "literary_style"]
        widgets = {
            "birth_date": DatePickerInput(),
            "death_date": DatePickerInput(),
        }


class ArrangerForm(PersonForm):
    class Meta:
        model = Arranger
        fields = PersonForm.Meta.fields + ["style"]
        widgets = {
            "birth_date": DatePickerInput(),
            "death_date": DatePickerInput(),
        }


class MusicianForm(PersonForm):
    class Meta:
        model = Musician
        fields = PersonForm.Meta.fields + ["instrument"]
        widgets = {
            "birth_date": DatePickerInput(),
            "death_date": DatePickerInput(),
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
                "date_joined": DatePickerInput(),
                "birth_date": DatePickerInput(),
                "death_date": DatePickerInput(),
            }


class SongForm(BaseForm):
    class Meta:
        model = Song
        fields = "__all__"

        widgets = {
            "year": DatePickerInput(),
        }


class RehearsalForm(BaseForm):
    class Meta:
        model = Rehearsal
        fields = ["subtitle","location", "parking", "calendar", "additional_notes",
                  "singers", "conductors", "songs", "duration_minutes", "attendance_count",
                  "is_cancelled"]
        widgets = {
            'calendar': DateTimePickerInput(),
            'duration_minutes': forms.NumberInput(attrs={'min': '1', 'placeholder': 'e.g. 180'}),
            'additional_notes': forms.Textarea(attrs={'rows': 3}),
            'singers': SingerWidget(attrs={'style': 'width: 100%;'}),
            'conductors': ModelSelect2MultipleWidget(model=Conductor, search_fields=["first_name__icontains"], attrs={'style': 'width: 100%;'}),
            'songs': SongWidget(attrs={'style': 'width: 100%;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
            "start_date": DatePickerInput(),
            "end_date": DatePickerInput(),
        }

class ImportFileForm(BaseForm):
    class Meta:
        model = ImportFile
        fields = [
            "title",
            "my_file"
        ]
