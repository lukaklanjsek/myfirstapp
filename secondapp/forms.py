from django import forms
# from .models import Song, Person, Member, Composer, Musician, Arranger, Poet, Tag
# from .models import Rehearsal, Activity, Conductor, Ensemble, ImportFile
from django_select2.forms import ModelSelect2MultipleWidget
#It is advised to always setup a separate cache server for Select2.
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, Organization, Person

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
    class Meta:
        model = Person
        fields = [
            "first_name",
            "last_name",
            "email",
            "address",
            "phone",
            "birth_date"
        ]
        widgets = {
            "birth_date": forms.DateInput(),
            "phone": forms.TelInput(),
        }


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ["name", "email", "address"]


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
#                   "is_cancelled"]
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
#         self.fields['is_cancelled'].label = "Mark as cancelled"
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
