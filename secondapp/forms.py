from django import forms
from .models import Rehearsal, Song, Person, Singer, Composer, Musician, Arranger, Poet, Tag


class PersonForm(forms.ModelForm):
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


class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = "__all__"


class RehearsalForm(forms.ModelForm):
    class Meta:
        model = Rehearsal
        fields = "__all__"


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = "__all__"