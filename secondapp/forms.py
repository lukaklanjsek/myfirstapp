from django import forms
from .models import Song, Person, Singer, Composer, Musician, Arranger, Poet, Tag
from .models import Rehearsal


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
            "tags",
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


class ComposerForm(PersonForm):
    class Meta:
        model = Composer
        fields = PersonForm.Meta.fields + ["work_style", "musical_era", "instruments"]


class PoetForm(PersonForm):
    class Meta:
        model = Poet
        fields = PersonForm.Meta.fields + ["writing_style", "literary_style"]


class ArrangerForm(PersonForm):
    class Meta:
        model = Arranger
        fields = PersonForm.Meta.fields + ["style", "instruments"]


class MusicianForm(PersonForm):
    class Meta:
        model = Musician
        fields = PersonForm.Meta.fields + ["instrument", "genre"]


class SongForm(BaseForm):
    class Meta:
        model = Song
        fields = "__all__"


class RehearsalForm(BaseForm):
    class Meta:
        model = Rehearsal
        fields = "__all__"
        widgets = {
            'calendar': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'duration_minutes': forms.NumberInput(attrs={'min': '1', 'placeholder': 'e.g. 180'}),
            'additional_notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['singers'].required = False
        self.fields['songs'].required = False
        self.fields['is_cancelled'].label = "Mark as cancelled"
        self.fields['duration_minutes'].label = "Expected duration (minutes) *"
        self.fields['attendance_count'].label = "Actual attendance count"


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name"]
