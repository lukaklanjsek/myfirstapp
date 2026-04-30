# views.py
import csv
import math
from dataclasses import field
from fileinput import filename
import sqlite3
from django.contrib.auth import logout, get_user_model
from django.shortcuts import redirect
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import PermissionDenied
from django.db import connection
from django.http import HttpRequest, HttpResponse, Http404, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.template.context_processors import request
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.sessions.models import Session
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.views import generic
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View, FormView, TemplateView
from django.views.generic.edit import DeleteView
from django.db.models import Count, Q, Prefetch
from django.apps import apps
from django.conf import settings
import os
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordContextMixin
from django.db import transaction
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
import datetime
from django.views.generic import FormView, TemplateView
from django.shortcuts import redirect
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import OrgMemberForm
from .models import Organization, Person, Membership, MembershipPeriod, Role, PersonSkill, PersonQuerySet, PersonRole
from .models import CustomUser, Organization, Person, Membership, Role, Song, Skill, Singer, Instrumentalist
from .models import Event, EventSong, Attendance, AttendanceType, EventType, Voice, Instrument, Quote, Project
from .forms import RegisterForm, OrganizationForm, PersonForm, SongForm, SkillForm, ProjectForm # SingerForm, InstrumentalistForm
from .forms import CustomUserCreationForm, EventForm, EventSongFormSet, AttendanceFormSet, AddAttendanceForm
from .forms import AddSongToEventForm, AddEventToProjectForm, QuoteForm, QuoteFormSet
from .forms import AddSongToProjectForm, AddGuestToProjectForm
from .mixins import  SkillListAndCreateMixin, SongOwnerMixin
from .permissions import AccessControl
from .utils import import_songs, import_persons, import_events, import_attendance, import_event_songs, combine_event_projects
# from .forms import RehearsalForm, Member, ComposerForm, PoetForm, ArrangerForm, MusicianForm, SongForm, TagForm, PersonForm, EnsembleForm, ActivityForm, ImportFileForm
# from .models import Rehearsal, Member, Composer, Poet, Arranger, Musician, Song, Ensemble, Activity, Conductor, ImportFile
# from .mixins import TagListAndCreateMixin, PersonRoleMixin, BreadcrumbMixin, LoginRequiredMixin



class SignUp(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "secondapp/signup.html"

    def form_valid(self, form):
        response = super().form_valid(form) #save the new user first

        Person.objects.create(
        user=self.object,
        email=self.object.email,
        first_name="",
        last_name="",
        )

        return response


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("secondapp:home")


class UserLoginView(LoginView):
    template_name = "registration/login.html"


class HomeView(generic.TemplateView):
    template_name = "secondapp/home.html"



@method_decorator(login_required, name='dispatch')
class PersonUpdateView(UpdateView):
    template_name = "secondapp/person_form2.html"
    form_class = PersonForm
    context_object_name = "person_create"
    success_url = reverse_lazy("secondapp:home")

    def dispatch(self, request, *args, **kwargs):
        url_username = self.kwargs.get("username")

        if url_username:
            try:
                self.organization = Organization.objects.get(user__username=url_username)

                # Check permission
                if not AccessControl.has_permission(request.user, "update", url_username):
                    return HttpResponseForbidden()
            except Organization.DoesNotExist:
                # No organization, this is a personal user
                self.organization = None
                # Only allow user to edit their own personal profile
                if request.user.username != url_username:
                    return HttpResponseForbidden()
        else:
            self.organization = None

        return super().dispatch(request, *args, **kwargs)

    # def get_object(self, queryset=None):
    #
    #     # single user
    #     if not self.organization:
    #         return get_object_or_404(
    #             Person,
    #             user=self.request.user
    #         )
    #
    #     # organization - ADMIN
    #     url_username = self.kwargs["username"]
    #     try:
    #         target_user = CustomUser.objects.get(username=url_username)
    #     except CustomUser.DoesNotExist:
    #         raise Http404("User not found")
    #
    #     return get_object_or_404(
    #         AccessControl.get_viewable_people_queryset(self.request.user)
    #         .filter(memberships__user=target_user),
    #         id=self.kwargs["pk"]
    #     )
    def get_object(self, queryset=None):
        person_id = self.kwargs.get("pk")

        if person_id:
            # Editing a specific organization person by ID
            url_username = self.kwargs["username"]
            try:
                target_user = CustomUser.objects.get(username=url_username)
            except CustomUser.DoesNotExist:
                raise Http404("User not found")

            return get_object_or_404(
                AccessControl.get_viewable_people_queryset(self.request.user)
                .filter(memberships__user=target_user),
                id=person_id
            )
        else:
            # Editing personal person (owner=None)
            # URL pattern: /<username>/person_form2/
            return get_object_or_404(
                Person,
                user=self.request.user,
                owner__isnull=True
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)

        # if user is connected, update email
        if self.object.user:
            self.object.user.email = self.object.email
            self.object.user.save()

        self.object.save()

        return redirect(self.get_success_url())


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "secondapp/index2.html"
    model = Person

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["memberships"] = Membership.objects.filter(person__user=user).select_related("user", "person", "role")
        return context


@method_decorator(login_required, name='dispatch')
class OrganizationDashboard(TemplateView):
    """Home page for specific organizations."""
    template_name = "secondapp/org_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        url_username = self.kwargs["username"]

        self.organization = get_object_or_404(
            Organization,
            user__username=url_username
        )

        self.viewer_roles = AccessControl.get_org_roles(
            request.user,
            url_username
        )

        if not self.viewer_roles:
            return HttpResponseForbidden()

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.organization

        context["org_memberships"] = AccessControl.get_visible_members(
            self.request.user,
            self.kwargs["username"]
        )

        return context


@method_decorator(login_required, name='dispatch')
class OrganizationCreateView(CreateView):
    template_name = "secondapp/organization_form.html"
    form_class = OrganizationForm
    context_object_name = "org_create"
    success_url = reverse_lazy("secondapp:home")

    def form_valid(self, form):
        # atomic transaction - creates everything at once:
        with transaction.atomic():
            the_admin = Person.objects.filter(user=self.request.user).first()

            # create auth account for org
            org_user = CustomUser.objects.create(
                username=slugify(form.cleaned_data["name"]),
                email=form.cleaned_data["email"],
            )
            org_user.set_unusable_password()
            org_user.save()

            # create org
            organization = form.save(commit=False)
            organization.user = org_user
            organization.save()

            # create admin person of the org
            person_admin = Person.objects.create(
                # user=organization.user,    # this Person belongs to the organization
                owner=the_admin,    #  this person is claimed by the creator of the organization
                email=the_admin.email,
                first_name=the_admin.first_name,
                last_name=the_admin.last_name,
            )

            # make an admin role into membership
            membership = Membership.objects.create(
                user=organization.user,
                person=person_admin,
            )

            person_role = PersonRole.objects.create(
                person = person_admin,
                role_id=Role.ADMIN
            )

            # track the admin into period
            MembershipPeriod.objects.create(
                user=organization.user,
                person=person_admin,
                role_id=Role.ADMIN,
                started_at=datetime.date.today()
            )

        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class OrgMemberListView(ListView):
    """Shows all members of a CustomUser."""
    template_name = "secondapp/org_member_list.html"
    context_object_name = "members"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        url_username = self.kwargs["username"]
        self.organization = get_object_or_404(
            CustomUser,
            username=url_username
        )

    def get_queryset(self):
        url_username = self.kwargs["username"]

        # Get all memberships for this organization
        visible_memberships = AccessControl.get_visible_members(
            self.request.user,
            url_username
        )

        queryset = visible_memberships.select_related('person').prefetch_related(
            'person__skills', 'person__roles',
            'person__singer_set__voice', 'person__instrumentalist_set__instrument',
        )

        q = self.request.GET.get('q', '').strip()
        if q:
            # When searching, include all matching results regardless of visibility filtering
            # but still respect the base membership access
            queryset = queryset.filter(
                Q(person__first_name__icontains=q) |
                Q(person__last_name__icontains=q) |
                Q(person__skills__title__icontains=q) |
                Q(person__singer__voice__name__icontains=q) |
                Q(person__instrumentalist__instrument__name__icontains=q)
            ).distinct()

        role_id = self.request.GET.get('role', '').strip()
        if role_id:
            queryset = queryset.filter(person__roles__id=int(role_id))

        sort_field_map = {
            'name': ('person__last_name', 'person__first_name'),
        }
        sort_key = self.request.GET.get('sort', 'name')
        reverse = self.request.GET.get('reverse', 'false') == 'true'
        fields = sort_field_map.get(sort_key, sort_field_map['name'])
        if reverse:
            fields = tuple(f'-{f}' for f in fields)
        return queryset.order_by(*fields)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.organization
        context["url_username"] = self.kwargs["username"]
        context["q"] = self.request.GET.get('q', '')
        context["current_sort"] = self.request.GET.get('sort', 'name')
        context["reverse"] = self.request.GET.get('reverse', 'false') == 'true'
        context["selected_role"] = self.request.GET.get('role', '')

        url_username = self.kwargs["username"]
        visible_members = AccessControl.get_visible_members(
            self.request.user,
            url_username
        )
        available_roles = Role.objects.filter(
            persons__in=visible_members.values_list('person', flat=True)
        ).distinct().order_by('title')
        context["available_roles"] = available_roles
        return context

@method_decorator(login_required, name="dispatch")
class OrgMemberDetailView(DetailView):
    """Shows details of a Person owned by Organization."""
    model = Person
    template_name = "secondapp/org_member_detail.html"
    context_object_name = "person"

    def dispatch(self, request, *args, **kwargs):
        """Handle permission checking before processing the request."""
        url_username = self.kwargs.get("username")

        if url_username:
            self.customuser = get_object_or_404(CustomUser, username=url_username)

            if request.user != self.customuser:
                self.has_edit_permission = AccessControl.can_edit_event(
                    request.user, self.customuser
                ).exists()

                if not self.has_edit_permission:  # CHANGED: Use cached result
                    return HttpResponseForbidden("You don't have permission to edit this event.")
        else:
            self.customuser = request.user

        return super().dispatch(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        url_username = self.kwargs["username"]

        context["url_username"] = url_username
        context["person_data"] = AccessControl.filter_person_details(
            self.request.user,
            self.object,
            url_username,
        )

        person = self.object
        if person.skills.filter(id=Skill.SINGER).exists():
            projects = Project.objects.filter(
                events__attendance__person=person
            ).distinct()

            singer_projects = []
            for project in projects:
                perf_attended = Attendance.objects.filter(
                    person=person,
                    event__project=project,
                    event__event_type_id__in=[EventType.PERFORMANCE, EventType.CONCERT, EventType.RECORDING],
                    attendance_type_id=AttendanceType.PRESENT,
                ).count()
                rehearsals_present = Attendance.objects.filter(
                    person=person,
                    event__project=project,
                    event__event_type_id=EventType.REHEARSAL,
                    attendance_type_id=AttendanceType.PRESENT,
                ).count()
                rehearsals_total = Event.objects.filter(
                    project=project,
                    event_type_id=EventType.REHEARSAL,
                ).count()
                singer_projects.append({
                    "project": project,
                    "performances_attended": perf_attended,
                    "rehearsals_present": rehearsals_present,
                    "rehearsals_total": rehearsals_total,
                })

            context["singer_projects"] = singer_projects

        return context


@method_decorator(login_required, name='dispatch')
class OrgMemberAddView( FormView):  # OrgMemberMixin,
    """Add new member."""
    template_name = "secondapp/org_member_form.html"
    form_class = OrgMemberForm

    def dispatch(self, request, *args, **kwargs):
        url_username = self.kwargs.get("username")

        if url_username:
            self.customuser = get_object_or_404(
                CustomUser,
                username=url_username
            )
            # Allow if viewing own account OR if has member access
            if request.user != self.customuser:
                member_queryset = AccessControl.can_view_member_list(
                    request.user,
                    self.customuser
                )
                if not member_queryset.exists():
                    return HttpResponseForbidden()


        else:
            self.customuser = None

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Pass preset to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['preset'] = self.kwargs.get('preset')
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['preset'] = self.kwargs.get('preset')
        return context

    def form_valid(self, form):
        with transaction.atomic():
            # 1. create new person
            person = self._create_person(form)

            # 2. add roles into membership
            self._add_roles(person, form.cleaned_data["roles"])

            # 3. add skills
            self._add_skills(person, form.cleaned_data["skills"])

            # 4. add voices
            self._add_voices(person, form.cleaned_data["voices"])

            # 5. add instruments
            self._add_instruments(person, form.cleaned_data["instruments"])

        next_url = self.request.GET.get('next', '')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={self.request.get_host()}):
            return redirect(next_url)
        return redirect("secondapp:org_member_list", username=self.kwargs["username"])

    def _create_person(self, form):
        """
        Create a new Person.
        - If adding to an customuser: create org person with owner
        - If adding to personal account: create personal person with owner=None
        """
        is_organization = Organization.objects.filter(user=self.customuser).exists()

        if is_organization:
            # adding members to an organization:
            person = Person.objects.create(
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                email=form.cleaned_data.get("email", ""),
                phone=form.cleaned_data.get("phone", ""),
                address=form.cleaned_data.get("address", ""),
                user=None,  # Belongs to organization
                owner=None  # Ownership not claimed yet
            )
        else:
            #  Adding to personal account (like adding a family member, poet, composer, etc.)
            # These are personal records that belong to the user but "user" is only for login
            person = Person.objects.create(
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                email=form.cleaned_data.get("email", ""),
                phone=form.cleaned_data.get("phone", ""),
                address=form.cleaned_data.get("address", ""),
                user=None,  # The personal user account
                owner=None  # Personal record, no owner
            )

        return person



    def _add_roles(self, person, selected_roles):
        """Create memberships for selected roles."""
        today = datetime.date.today()

        # Create the base membership (only once per person-org relationship)
        membership, created = Membership.objects.get_or_create(
            user=self.customuser,
            person=person
        )

        for role in selected_roles:
            # Create PersonRole to assign the role to the person
            PersonRole.objects.create(
                person=person,
                role=role
            )

            # Track when they started this role
            MembershipPeriod.objects.create(
                user=self.customuser,
                person=person,
                role=role,
                started_at=today
            )

    def _add_skills(self, person, selected_skills):
        """Create PersonSkill entry for selected skills."""
        for skill in selected_skills:
            PersonSkill.objects.create(
                person=person,
                skill=skill
            )

    def _add_voices(self, person, selected_voices):
        """Create Singer entries and ensure 'singer' skill is added."""
        if not selected_voices:
            return

        # Create Singer entries for each selected voice
        for voice in selected_voices:
            Singer.objects.create(
                person=person,
                voice=voice
            )

        # Automatically add 'singer' skill if voices were selected
        singer_skill = Skill.objects.filter(title__iexact='singer').first()
        if singer_skill:
            PersonSkill.objects.get_or_create(
                person=person,
                skill=singer_skill
            )

    def _add_instruments(self, person, selected_instruments):
        """Create Instrumentalist entries and ensure 'instrumentalist' skill is added."""
        if not selected_instruments:
            return

        # Create Instrumentalist entries for each selected instrument
        for instrument in selected_instruments:
            Instrumentalist.objects.create(
                person=person,
                instrument=instrument
            )

        # Automatically add 'instrumentalist' skill if instruments were selected
        instrumentalist_skill = Skill.objects.filter(title__iexact='instrumentalist').first()
        if instrumentalist_skill:
            PersonSkill.objects.get_or_create(
                person=person,
                skill=instrumentalist_skill
            )





@method_decorator(login_required, name='dispatch')
class OrgMemberEditView( FormView):  # OrgMemberMixin,
    """Edit existing member. Admin can edit everybody, user can edit its own."""
    template_name = "secondapp/org_member_form.html"
    form_class = OrgMemberForm


    def dispatch(self, request, *args, **kwargs):
        url_username = self.kwargs["username"]
        # print("print orgmembereditview dispatch url_username:", url_username)

        self.customuser = get_object_or_404(
            CustomUser,
            username=url_username
        )
        # print("orgmembereditview dispatch customuser", self.customuser)

        self.person = get_object_or_404(Person, pk=self.kwargs["pk"])
        # print("orgmembereditview dispatch person", self.person)

        viewer_role = AccessControl.get_org_roles(
            request.user,
            url_username
        )
        # print("orgmembereditview dispatch viewer_role", viewer_role)

        is_admin = viewer_role.filter(id=Role.ADMIN).exists()
        is_owner = self.person.user == request.user

        # print("orgmembereditview dispatch is_admin, is_owner", is_admin, is_owner)

        if not (is_admin or is_owner):
            raise PermissionDenied("No permission to edit")

        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        # pre-fill form with existing data
        form = super().get_form(form_class)

        if self.request.method == "GET":
            # current roles in THIS organization
            current_role_ids = self.person.roles.values_list("id", flat=True)

            # current skills
            current_skill_ids = self.person.skills.values_list(
                "id", flat=True
            )

            # current voices
            current_voice_ids = Voice.objects.filter(
                singer__person=self.person
            ).values_list("id", flat=True)

            # current instruments
            current_instrument_ids = Instrument.objects.filter(
                instrumentalist__person=self.person
            ).values_list("id", flat=True)

            # dict of the checkboxes
            form.initial = {
                # person info
                "first_name": self.person.first_name,
                "last_name": self.person.last_name,
                "email": self.person.email,
                "phone": self.person.phone,
                "address": self.person.address,
                # m2m relationships
                "roles": current_role_ids,
                "skills": current_skill_ids,
                "voices": current_voice_ids,
                "instruments": current_instrument_ids,
            }

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.customuser
        return context

    def form_valid(self, form):
        with transaction.atomic():
            # 1. update person info
            self._update_person_info(form)

            # 2. update roles
            self._update_roles(form.cleaned_data["roles"])

            # 3. update skills
            self._update_skills(form.cleaned_data["skills"])

            # 4. update voices
            self._update_voices(form.cleaned_data["voices"])

            # 5. update instruments
            self._update_instruments(form.cleaned_data["instruments"])

        return redirect("secondapp:org_member_list",username=self.kwargs["username"])

    def _update_person_info(self, form):
        """update personal info"""
        self.person.first_name = form.cleaned_data["first_name"]
        self.person.last_name = form.cleaned_data["last_name"]
        self.person.email = form.cleaned_data.get("email", "")
        self.person.phone = form.cleaned_data.get("phone", "")
        self.person.address = form.cleaned_data.get("address", "")
        self.person.save()

    def _update_roles(self, new_roles):
        """sync roles - add new ones, remove old ones"""
        today = datetime.date.today()

        # Get current roles for this person
        current_role_ids = set(self.person.roles.values_list("id", flat=True))

        # New roles from form
        new_role_ids = {role.id for role in new_roles}

        # Get or create the base membership (the relationship between org user and person)
        membership, _ = Membership.objects.get_or_create(
            user=self.customuser,
            person=self.person
        )

        # Add new roles
        for role_id in (new_role_ids - current_role_ids):
            PersonRole.objects.create(
                person=self.person,
                role_id=role_id
            )
            MembershipPeriod.objects.create(
                user=self.customuser,
                person=self.person,
                role_id=role_id,
                started_at=today
            )

        # Remove roles
        removed_role_ids = current_role_ids - new_role_ids
        if removed_role_ids:
            # Close open periods for removed roles
            MembershipPeriod.objects.filter(
                user=self.customuser,
                person=self.person,
                role_id__in=removed_role_ids,
                ended_at__isnull=True
            ).update(ended_at=today)

            # Delete the PersonRole entries
            PersonRole.objects.filter(
                person=self.person,
                role_id__in=removed_role_ids
            ).delete()

    def _update_skills(self, new_skills):
        """sync skills - add new, remove old"""
        # current skills
        current_skills = PersonSkill.objects.filter(person=self.person)
        current_skill_ids = set(current_skills.values_list("skill_id", flat=True))

        # new skills
        new_skill_ids = {skill.id for skill in new_skills}

        # do the magic
        for skill_id in (new_skill_ids - current_skill_ids):
            PersonSkill.objects.create(
                person=self.person,
                skill_id=skill_id
            )

        # remove old skills
        removed_skill_ids = current_skill_ids - new_skill_ids
        if removed_skill_ids:
            current_skills.filter(skill_id__in=removed_skill_ids).delete()

    def _update_voices(self, new_voices):
        """Sync voices - add new ones, remove old ones."""
        # Current voices
        current_singers = Singer.objects.filter(person=self.person)
        current_voice_ids = set(current_singers.values_list("voice_id", flat=True))

        # New voices from form
        new_voice_ids = {voice.id for voice in new_voices}

        # Add new voices
        for voice_id in (new_voice_ids - current_voice_ids):
            Singer.objects.create(
                person=self.person,
                voice_id=voice_id
            )

        # Remove old voices
        removed_voice_ids = current_voice_ids - new_voice_ids
        if removed_voice_ids:
            current_singers.filter(voice_id__in=removed_voice_ids).delete()

        # Handle 'singer' skill
        singer_skill = Skill.objects.filter(title__iexact='singer').first()
        if singer_skill:
            if new_voices:
                # If voices selected, ensure singer skill exists
                PersonSkill.objects.get_or_create(
                    person=self.person,
                    skill=singer_skill
                )
            else:
                # If no voices selected, remove singer skill
                PersonSkill.objects.filter(
                    person=self.person,
                    skill=singer_skill
                ).delete()

    def _update_instruments(self, new_instruments):
        """Sync instruments - add new ones, remove old ones."""
        # Current instruments
        current_instrumentalists = Instrumentalist.objects.filter(person=self.person)
        current_instrument_ids = set(current_instrumentalists.values_list("instrument_id", flat=True))

        # New instruments from form
        new_instrument_ids = {instrument.id for instrument in new_instruments}

        # Add new voices
        for instrument_id in (new_instrument_ids - current_instrument_ids):
            Instrumentalist.objects.create(
                person=self.person,
                instrument_id=instrument_id
            )

        # Remove old instruments
        removed_instrument_ids = current_instrument_ids - new_instrument_ids
        if removed_instrument_ids:
            current_instrumentalists.filter(instrument_id__in=removed_instrument_ids).delete()

        # Handle 'instrumentalist' skill
        instrumentalist_skill = Skill.objects.filter(title__iexact='instrumentalist').first()
        if instrumentalist_skill:
            if new_instruments:
                # If instruments selected, ensure instrumentalist skill exists
                PersonSkill.objects.get_or_create(
                    person=self.person,
                    skill=instrumentalist_skill
                )
            else:
                # If no voices selected, remove singer skill
                PersonSkill.objects.filter(
                    person=self.person,
                    skill=instrumentalist_skill
                ).delete()



@method_decorator(login_required, name='dispatch')
class SongListView(SongOwnerMixin, ListView):
    model = Song
    template_name = "secondapp/song_dashboard.html"
    context_object_name = "songs"
    permission_check_method = AccessControl.can_view_song_list

    def get_queryset(self):
        qs = AccessControl.can_view_song_list(self.request.user, self.owner_user)
        q = self.request.GET.get('q', '').strip()
        if q:
            if q.isdigit():
                qs = qs.filter(internal_id=int(q))
            else:
                qs = qs.filter(
                    Q(title__icontains=q) |
                    Q(composer__last_name__icontains=q) |
                    Q(keywords__icontains=q)
                ).distinct()

        # Handle sorting
        sort = self.request.GET.get('sort', 'id')
        reverse = self.request.GET.get('reverse', 'false') == 'true'

        sort_field_map = {
            'id': 'internal_id',
            'title': 'title',
            'composer': 'composer__last_name',
        }

        sort_field = sort_field_map.get(sort, 'internal_id')
        if reverse:
            sort_field = f'-{sort_field}'

        return qs.order_by(sort_field)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["url_username"] = self.owner_user.username
        context["q"] = self.request.GET.get('q', '')
        context["current_sort"] = self.request.GET.get('sort', 'id')
        context["reverse"] = self.request.GET.get('reverse', 'false') == 'true'
        return context


@method_decorator(login_required, name='dispatch')
class SongDetailView(SongOwnerMixin, DetailView):
    model = Song
    template_name = "secondapp/song_page.html"
    context_object_name = "song"
    permission_check_method = AccessControl.can_view_song

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_username'] = self.owner_user.username

        song = self.get_object()
        events = Event.objects.filter(
            eventsong__song=song
        ).order_by('-started_at').distinct()
        context['events'] = events

        return context


@method_decorator(login_required, name='dispatch')
class SongCreateView(SongOwnerMixin, CreateView):
    form_class = SongForm
    template_name = "secondapp/song_form2.html"
    permission_check_method = AccessControl.can_manage_song

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.owner_user
        return kwargs

    def get_context_data(self, quote_formset=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_username'] = self.owner_user.username
        if quote_formset is not None:
            context['quote_formset'] = quote_formset
        elif self.request.POST:
            context['quote_formset'] = QuoteFormSet(self.request.POST, prefix='quotes')
        else:
            context['quote_formset'] = QuoteFormSet(prefix='quotes')
        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'add_kw_row':
            self.object = None
            form = self.get_form()
            post_data = request.POST.copy()
            total = int(post_data.get('quotes-TOTAL_FORMS', 0))
            post_data['quotes-TOTAL_FORMS'] = total + 1
            kf = QuoteFormSet(post_data, prefix='quotes')
            return self.render_to_response(self.get_context_data(form=form, quote_formset=kf))
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.owner_user
        self.object = form.save()
        kf = QuoteFormSet(self.request.POST, instance=self.object, prefix='quotes')
        if kf.is_valid():
            kf.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        next_url = self.request.POST.get('next') or self.request.GET.get('next', '')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={self.request.get_host()}):
            return next_url
        return reverse_lazy("secondapp:song_page", kwargs={
            "username": self.owner_user.username,
            "pk": self.object.pk
        })


@method_decorator(login_required, name='dispatch')
class SongUpdateView(SongOwnerMixin, UpdateView):
    form_class = SongForm
    template_name = "secondapp/song_form2.html"
    permission_check_method = AccessControl.can_manage_song

    def get_queryset(self):
        return Song.objects.filter(user=self.owner_user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.owner_user
        return kwargs

    def get_context_data(self, quote_formset=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_username'] = self.owner_user.username
        if quote_formset is not None:
            context['quote_formset'] = quote_formset
        elif self.request.POST:
            context['quote_formset'] = QuoteFormSet(self.request.POST, instance=self.object, prefix='quotes')
        else:
            context['quote_formset'] = QuoteFormSet(instance=self.object, prefix='quotes')
        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'add_kw_row':
            self.object = self.get_object()
            form = self.get_form()
            post_data = request.POST.copy()
            total = int(post_data.get('quotes-TOTAL_FORMS', 0))
            post_data['quotes-TOTAL_FORMS'] = total + 1
            kf = QuoteFormSet(post_data, instance=self.object, prefix='quotes')
            return self.render_to_response(self.get_context_data(form=form, quote_formset=kf))
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.owner_user
        self.object = form.save()
        kf = QuoteFormSet(self.request.POST, instance=self.object, prefix='quotes')
        if kf.is_valid():
            kf.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("secondapp:song_page", kwargs={
            "username": self.owner_user.username,
            "pk": self.object.pk
        })


@method_decorator(login_required, name='dispatch')
class SongDeleteView(SongOwnerMixin, DeleteView):
    model = Song
    template_name = "secondapp/song_confirm_delete.html"
    permission_check_method = AccessControl.can_manage_song

    def get_success_url(self):
        return reverse_lazy("secondapp:song_dashboard", kwargs={
            "username": self.owner_user.username
        })

class SkillListAndCreateView(SkillListAndCreateMixin, View):
    pass


@method_decorator(login_required, name='dispatch')
class EventCreateView(CreateView):
    """Step 1: Create event with basic info only"""
    model = Event
    form_class = EventForm
    template_name = 'secondapp/event_create.html'

    def dispatch(self, request, *args, **kwargs):
        url_username = self.kwargs.get("username")

        if url_username:
            self.customuser = get_object_or_404(
                CustomUser,
                username=url_username
            )
            # Allow if viewing own account OR if has member access
            if request.user != self.customuser:
                member_queryset = AccessControl.can_add_event(
                    request.user,
                    self.customuser
                )
                if not member_queryset.exists():
                    return HttpResponseForbidden()

        else:
            self.customuser = None


        return super().dispatch(request, *args, **kwargs)


    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # kwargs['username'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user_to_assign = self.customuser if self.customuser else self.request.user
        form.instance.user = user_to_assign
        response = super().form_valid(form)

        # Initialize attendance records for all active performers at the event date
        event = self.object
        event_date = event.started_at or timezone.now()
        unknown_type = AttendanceType.objects.get(pk=AttendanceType.UNKNOWN)
        members = Person.objects.active_performers(user_to_assign, event_date)
        Attendance.objects.bulk_create(
            [Attendance(event=event, person=m, attendance_type=unknown_type) for m in members],
            ignore_conflicts=True,
        )
        return response


    # def form_valid(self, form):
    #     form.instance.user = self.request.user
    #     response = super().form_valid(form)
    #     # Redirect to update view to add songs and attendance
    #     return redirect('secondapp:event_update', username=self.kwargs["username"], pk=self.object.pk)
    #
    def get_success_url(self):
        return reverse_lazy("secondapp:event_update", kwargs={
            "username": self.customuser.username,
            "pk": self.object.pk
        })

@method_decorator(login_required, name='dispatch')
class EventUpdateView(UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'secondapp/event_update.html'

    def dispatch(self, request, *args, **kwargs):
        url_username = self.kwargs.get("username")
        self.customuser = get_object_or_404(CustomUser, username=url_username) if url_username else request.user

        if request.user != self.customuser:
            self.is_admin = AccessControl.can_add_event(
                request.user, self.customuser
            ).filter(person__roles__id=Role.ADMIN).exists()

            has_access = self.is_admin or AccessControl.can_edit_event(request.user, self.customuser).exists()
            if not has_access:
                return HttpResponseForbidden("You don't have permission to access this page.")

            if request.method == 'POST' and not self.is_admin:
                return HttpResponseForbidden("Only admins can save event changes.")
        else:
            self.is_admin = True

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.customuser
        return kwargs

    def post(self, request, *args, **kwargs):
        """Handle reorder actions before form validation."""
        if request.POST.get('reorder'):
            self.object = self.get_object()
            self._reorder_songs_db(self.object)
            # Always redirect after reorder, don't process form
            event_update_url = reverse('secondapp:event_update', kwargs={
                'username': self.kwargs['username'],
                'pk': self.object.pk,
            })
            return redirect(event_update_url)
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        """Return only events belonging to the organization/user from URL."""
        return Event.objects.filter(
            user=self.customuser
        ).select_related('user', 'event_type').prefetch_related(
            'eventsong_set__song',
            'attendance_set__person'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object
        event_date = event.started_at or timezone.now()

        members = Person.objects.active_performers(
            self.customuser, event_date
        ).select_related('user').prefetch_related('roles')

        if not hasattr(self, '_song_formset'):
            from django.db.models import Min, Case, When, Value, IntegerField
            attendance_qs = event.attendance_set.select_related(
                'person', 'attendance_type'
            ).annotate(
                voice_order=Min('person__singer__voice__id'),
                instrument_order=Min('person__instrumentalist__instrument__id'),
            ).order_by(
                Case(
                    When(voice_order__isnull=False, then=Value(0)),
                    When(instrument_order__isnull=False, then=Value(1)),
                    default=Value(2),
                    output_field=IntegerField(),
                ),
                'voice_order',
                'instrument_order',
                'person__last_name',
                'person__first_name',
            )
            song_qs = event.eventsong_set.all().order_by('order')
            if self.request.POST:
                self._song_formset = EventSongFormSet(
                    self.request.POST,
                    instance=event,
                    queryset=song_qs,
                )
                self._attendance_formset = AttendanceFormSet(
                    self.request.POST,
                    instance=event,
                    queryset=attendance_qs,
                    form_kwargs={'person_queryset': members},
                )
            else:
                self._song_formset = EventSongFormSet(
                    instance=event,
                    queryset=song_qs,
                )
                self._attendance_formset = AttendanceFormSet(
                    instance=event,
                    queryset=attendance_qs,
                    form_kwargs={'person_queryset': members},
                )

        search_q = self.request.GET.get('q', '')
        show_add_form = self.request.GET.get('add_participant') == '1' and self.is_admin
        show_add_song = self.is_admin
        song_search_q = self.request.GET.get('song_q', '')

        context['song_formset'] = self._song_formset
        context['attendance_formset'] = self._attendance_formset
        context['attendance_types'] = AttendanceType.objects.all()
        context['url_username'] = self.kwargs.get('username')
        context['is_admin'] = self.is_admin
        context['admin_override'] = self.request.GET.get('admin_override') == 'true' and self.is_admin
        context['show_add_form'] = show_add_form
        context['search_q'] = search_q
        context['show_add_song'] = show_add_song
        context['song_search_q'] = song_search_q
        context['add_form'] = AddAttendanceForm(
            org_user=self.customuser,
            event=event,
            search_q=search_q,
        ) if show_add_form else None
        context['add_song_form'] = AddSongToEventForm(
            org_user=self.customuser,
            event=event,
            search_q=song_search_q,
        ) if show_add_song else None
        return context



    def _save_songs(self, event, song_formset):
        EventSong.objects.filter(event=event).delete()
        valid_songs = [
            {
                'song': f.cleaned_data['song'],
                'encore': f.cleaned_data.get('encore', False),
                'instance': f.instance,
            }
            for f in song_formset.forms
            if f.cleaned_data and not f.cleaned_data.get('DELETE') and f.cleaned_data.get('song')
        ]
        for idx, song_data in enumerate(valid_songs):
            EventSong.objects.create(
                event=event,
                song=song_data['song'],
                order=idx + 1,
                encore=song_data['encore'],
            )

    def _reorder_songs_db(self, event):
        """Reorder songs in the database based on reorder button click."""
        reorder_value = self.request.POST.get('reorder', '').strip()
        if not reorder_value or not reorder_value.startswith('song_'):
            return

        try:
            parts = reorder_value.split('_')
            song_pk = int(parts[1])
            direction = '_'.join(parts[2:])  # handles "up_one", "up_all", "down_one", "down_all"
        except (ValueError, IndexError):
            return

        songs = list(event.eventsong_set.all().order_by('order'))
        if not songs:
            return

        song_idx = None
        for idx, song in enumerate(songs):
            if song.pk == song_pk:
                song_idx = idx
                break

        if song_idx is None:
            return

        # Perform the reordering
        moved = False
        if direction == 'up_one' and song_idx > 0:
            songs[song_idx], songs[song_idx - 1] = songs[song_idx - 1], songs[song_idx]
            moved = True
        elif direction == 'up_all' and song_idx > 0:
            songs.insert(0, songs.pop(song_idx))
            moved = True
        elif direction == 'down_one' and song_idx < len(songs) - 1:
            songs[song_idx], songs[song_idx + 1] = songs[song_idx + 1], songs[song_idx]
            moved = True
        elif direction == 'down_all' and song_idx < len(songs) - 1:
            songs.append(songs.pop(song_idx))
            moved = True

        if not moved:
            return

        # Update order in database using temporary negative values to avoid constraint violations
        with transaction.atomic():
            # First, set all to temporary negative values
            for idx, song in enumerate(songs):
                song.order = -(idx + 1)
                song.save(update_fields=['order'])
            # Then, set to final positive values
            for idx, song in enumerate(songs):
                song.order = idx + 1
                song.save(update_fields=['order'])

    def form_valid(self, form):
        self.get_context_data()  # ensures formsets are built and cached on self
        admin_override = self.request.POST.get('admin_override') == 'true' and self.is_admin

        if not self._song_formset.is_valid():
            messages.error(self.request, "Please fix errors in the songs section.")
            return self.form_invalid(form)

        if not self._attendance_formset.is_valid():
            messages.error(self.request, "Please fix errors in the attendance section.")
            return self.form_invalid(form)

        with transaction.atomic():
            self.object = form.save()
            self._save_songs(self.object, self._song_formset)
            self._attendance_formset.instance = self.object
            self._attendance_formset.save()

        action = self.request.POST.get('action', 'save')
        event_update_url = reverse('secondapp:event_update', kwargs={
            'username': self.kwargs['username'],
            'pk': self.object.pk,
        })

        if action == 'show_add_form':
            return redirect(event_update_url + '?add_participant=1')

        if action == 'save_and_add_song':
            return redirect(event_update_url + '?add_song=1')

        if action == 'add_member':
            add_url = reverse('secondapp:org_member_add', kwargs={
                'username': self.kwargs['username'],
            })
            return redirect(f'{add_url}?next={event_update_url}')

        if admin_override:
            messages.success(self.request, "Event updated successfully! (Admin override used)")
        else:
            messages.success(self.request, "Event updated successfully!")
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        if form.errors:
            messages.error(self.request, f"Event form errors: {form.errors}")
        messages.error(self.request, "There was an error updating the event. Please check the form below.")
        return super().form_invalid(form)

    def get_success_url(self):
        """Redirect to event detail page after successful update."""  # ADDED: Docstring
        return reverse_lazy('secondapp:event_detail', kwargs={
            'username': self.kwargs.get('username'),
            'pk': self.object.pk
        })


@method_decorator(login_required, name="dispatch")
class EventListView(ListView):
    template_name = "secondapp/event_list.html"
    context_object_name = "events"
    model = Event
    # ordering = ['-started_at']


    def get_queryset(self):
        url_username = self.kwargs.get("username")
        customuser = get_object_or_404(CustomUser, username=url_username)
        return Event.objects.filter(user=customuser).order_by('-started_at')


@method_decorator(login_required, name='dispatch')
class EventDetailView(DetailView):
    model = Event
    template_name = 'secondapp/event_detail.html'

    def get_queryset(self):
        url_username = self.kwargs.get("username")
        customuser = get_object_or_404(CustomUser, username=url_username)
        return Event.objects.filter(user=customuser).prefetch_related(
            'attendance_set__person',
            'attendance_set__attendance_type',
            'eventsong_set__song__composer',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_username'] = self.kwargs.get('username')
        context['attendance_types'] = AttendanceType.objects.all()
        context['my_person'] = AccessControl.get_member_person(self.request.user, self.object.user)
        from django.db.models import Min, Case, When, Value, IntegerField
        context['attendances'] = self.object.attendance_set.select_related(
            'person', 'attendance_type'
        ).annotate(
            voice_order=Min('person__singer__voice__id'),
            instrument_order=Min('person__instrumentalist__instrument__id'),
        ).order_by(
            Case(
                When(voice_order__isnull=False, then=Value(0)),
                When(instrument_order__isnull=False, then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            ),
            'voice_order',
            'instrument_order',
            'person__last_name',
            'person__first_name',
        )
        context['is_admin'] = AccessControl.can_add_event(
            self.request.user, self.object.user
        ).filter(person__roles__id=Role.ADMIN).exists()
        return context

@require_POST
@login_required
def self_attendance_update(request, username, event_pk):
    org_user = get_object_or_404(CustomUser, username=username)
    event = get_object_or_404(Event, pk=event_pk, user=org_user)

    my_person = AccessControl.get_member_person(request.user, org_user)
    if not my_person:
        return HttpResponseForbidden("You are not a member of this organization.")

    attendance = get_object_or_404(Attendance, event=event, person=my_person)
    attendance_type = get_object_or_404(AttendanceType, pk=request.POST.get('attendance_type'))
    attendance.attendance_type = attendance_type
    attendance.save()

    return redirect('secondapp:event_detail', username=username, pk=event_pk)


@require_POST
@login_required
def event_add_attendance(request, username, pk):
    org_user = get_object_or_404(CustomUser, username=username)
    event = get_object_or_404(Event, pk=pk, user=org_user)

    is_admin = AccessControl.can_add_event(
        request.user, org_user
    ).filter(person__roles__id=Role.ADMIN).exists()
    if not is_admin:
        return HttpResponseForbidden("Only admins can add participants.")

    form = AddAttendanceForm(request.POST, org_user=org_user, event=event)
    if form.is_valid():
        Attendance.objects.get_or_create(
            event=event,
            person=form.cleaned_data['person'],
            defaults={'attendance_type': form.cleaned_data['attendance_type']},
        )

    return redirect('secondapp:event_update', username=username, pk=pk)


@method_decorator(login_required, name='dispatch')
class AttendanceDeleteView(DeleteView):
    model = Attendance
    template_name = "secondapp/attendance_confirm_delete.html"

    def dispatch(self, request, *args, **kwargs):
        url_username = self.kwargs['username']
        self.org_user = get_object_or_404(CustomUser, username=url_username)
        is_admin = AccessControl.can_add_event(
            request.user, self.org_user
        ).filter(person__roles__id=Role.ADMIN).exists()
        if not is_admin:
            return HttpResponseForbidden("Only admins can delete participants.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        event = get_object_or_404(Event, pk=self.kwargs['event_pk'], user=self.org_user)
        return Attendance.objects.filter(event=event)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_username'] = self.kwargs['username']
        context['event'] = self.object.event
        return context

    def get_success_url(self):
        return reverse_lazy('secondapp:event_update', kwargs={
            'username': self.kwargs['username'],
            'pk': self.kwargs['event_pk'],
        })


@require_POST
@login_required
def event_add_song(request, username, pk):
    from django.db.models import Max
    org_user = get_object_or_404(CustomUser, username=username)
    event = get_object_or_404(Event, pk=pk, user=org_user)

    is_admin = AccessControl.can_add_event(
        request.user, org_user
    ).filter(person__roles__id=Role.ADMIN).exists()
    if not is_admin:
        return HttpResponseForbidden("Only admins can add songs to events.")

    form = AddSongToEventForm(request.POST, org_user=org_user, event=event)
    if form.is_valid():
        next_order = (event.eventsong_set.aggregate(Max('order'))['order__max'] or 0) + 1
        EventSong.objects.create(
            event=event,
            song=form.cleaned_data['song'],
            order=next_order,
            encore=form.cleaned_data.get('encore', False),
        )

    return redirect('secondapp:event_update', username=username, pk=pk)


@require_POST
@login_required
def project_add_event(request, username, pk):
    org_user = get_object_or_404(CustomUser, username=username)
    project = get_object_or_404(Project, pk=pk, user=org_user)

    is_admin = AccessControl.can_add_event(
        request.user, org_user
    ).filter(person__roles__id=Role.ADMIN).exists()
    if not is_admin:
        return HttpResponseForbidden("Only admins can add events to projects.")

    form = AddEventToProjectForm(request.POST, org_user=org_user, project=project)
    if form.is_valid():
        event = form.cleaned_data['event']
        event.project = project
        event.save()

    return redirect('secondapp:project_update', username=username, pk=pk)


@require_POST
@login_required
def project_remove_event(request, username, pk, event_pk):
    org_user = get_object_or_404(CustomUser, username=username)
    project = get_object_or_404(Project, pk=pk, user=org_user)
    event = get_object_or_404(Event, pk=event_pk, project=project)

    is_admin = AccessControl.can_add_event(
        request.user, org_user
    ).filter(person__roles__id=Role.ADMIN).exists()
    if not is_admin:
        return HttpResponseForbidden("Only admins can remove events from projects.")

    event.project = None
    event.save()

    return redirect('secondapp:project_update', username=username, pk=pk)


@require_POST
@login_required
def project_add_song(request, username, pk):
    org_user = get_object_or_404(CustomUser, username=username)
    project = get_object_or_404(Project, pk=pk, user=org_user)

    form = AddSongToProjectForm(request.POST, org_user=org_user, project=project)
    if form.is_valid():
        project.songs.add(form.cleaned_data['song'])

    return redirect('secondapp:project_update', username=username, pk=pk)


@require_POST
@login_required
def project_remove_song(request, username, pk, song_pk):
    org_user = get_object_or_404(CustomUser, username=username)
    project = get_object_or_404(Project, pk=pk, user=org_user)
    project.songs.remove(song_pk)

    return redirect('secondapp:project_update', username=username, pk=pk)


@require_POST
@login_required
def project_add_guest(request, username, pk):
    org_user = get_object_or_404(CustomUser, username=username)
    project = get_object_or_404(Project, pk=pk, user=org_user)

    form = AddGuestToProjectForm(request.POST, org_user=org_user, project=project)
    if form.is_valid():
        project.guests.add(form.cleaned_data['guest'])

    return redirect('secondapp:project_update', username=username, pk=pk)


@require_POST
@login_required
def project_remove_guest(request, username, pk, guest_pk):
    org_user = get_object_or_404(CustomUser, username=username)
    project = get_object_or_404(Project, pk=pk, user=org_user)
    project.guests.remove(guest_pk)

    return redirect('secondapp:project_update', username=username, pk=pk)


@method_decorator(login_required, name='dispatch')
class SongQuoteView(SongOwnerMixin, View):
    """Manage quotes for a specific song. Supports ?next= redirect after save."""
    template_name = 'secondapp/song_quotes.html'
    permission_check_method = AccessControl.can_manage_song

    def _get_song(self, pk):
        song = get_object_or_404(Song, pk=pk, user=self.owner_user)
        if not AccessControl.can_manage_song(self.request.user, song):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return song

    def _next_url(self, request, username, pk):
        next_url = request.GET.get('next') or request.POST.get('next', '')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return next_url
        return reverse('secondapp:song_page', kwargs={'username': username, 'pk': pk})

    def get(self, request, username, pk):
        song = self._get_song(pk)
        formset = QuoteFormSet(instance=song, prefix='quotes')
        return render(request, self.template_name, {
            'song': song,
            'formset': formset,
            'url_username': username,
            'next': request.GET.get('next', ''),
        })

    def post(self, request, username, pk):
        song = self._get_song(pk)
        if request.POST.get('action') == 'add_kw_row':
            post_data = request.POST.copy()
            total = int(post_data.get('quotes-TOTAL_FORMS', 0))
            post_data['quotes-TOTAL_FORMS'] = total + 1
            formset = QuoteFormSet(post_data, instance=song, prefix='quotes')
            return render(request, self.template_name, {
                'song': song,
                'formset': formset,
                'url_username': username,
                'next': request.POST.get('next', ''),
            })
        formset = QuoteFormSet(request.POST, instance=song, prefix='quotes')
        if formset.is_valid():
            formset.save()
            return redirect(self._next_url(request, username, pk))
        return render(request, self.template_name, {
            'song': song,
            'formset': formset,
            'url_username': username,
            'next': request.POST.get('next', ''),
        })


@method_decorator(login_required, name="dispatch")
class AttendanceDashboardView(View):
    template_name = 'secondapp/attendance.html'

    def dispatch(self, request, *args, **kwargs):
        """Handle permission checking before processing the request."""
        url_username = self.kwargs.get("username")
        self.org_user = get_object_or_404(CustomUser, username=url_username)

        if request.user != self.org_user:
            has_permission = AccessControl.can_edit_event(
                request.user, self.org_user
            ).exists()

            if not has_permission:
                return HttpResponseForbidden("You don't have permission to view this dashboard.")

        return super().dispatch(request, *args, **kwargs)

    def _fetch_events(self, event_limit, start_date, end_date, include_prefetch=True):
        """
        Fetch and organize events for display.
        Returns (events list, editable_event_id, grayed_out_event_ids)

        Filter logic:
        - If start_date AND end_date: use date range, return all events in range
        - Otherwise: show one future event (if available), one present event (current or most recent past), and all other past events
        - Only one event is editable (either current event or most recent past)
        """
        now = timezone.now()

        # Build base query with optimization
        base_query = Event.objects.filter(
            user=self.org_user
        ).select_related('event_type')

        if include_prefetch:
            base_query = base_query.prefetch_related(
                'attendance_set__person',
                'attendance_set__attendance_type'
            )

        # Apply date filters if provided
        if start_date and end_date:
            base_query = base_query.filter(
                started_at__date__gte=start_date,
                started_at__date__lte=end_date
            )

        # Split into past and future events
        past_qs = base_query.filter(started_at__lt=now).order_by('-started_at')
        future_qs = base_query.filter(started_at__gte=now).order_by('started_at')

        # Fetch events: date range takes all, otherwise show simplified view
        if start_date and end_date:
            # Date range mode: fetch all events in range
            past_events = list(past_qs)
            future_events = list(future_qs)
        else:
            # Simplified mode: one future event, limited past events
            future_events = list(future_qs[:1])
            past_events = list(past_qs[:event_limit])

        # Final list: oldest past → most recent past → soonest future
        events = list(reversed(past_events)) + future_events

        # Determine which event is editable: current event or most recent past
        editable_event = None

        # First, check if there's a current event (started but not finished)
        current_event = base_query.filter(
            started_at__lte=now,
            ended_at__gt=now
        ).first()

        if current_event:
            editable_event = current_event
        elif past_events:
            editable_event = past_events[0]  # Most recent past event

        editable_event_id = editable_event.id if editable_event else None

        # Mark non-editable past events as grayed out (for POST skip logic)
        grayed_out_event_ids = set()
        for event in events:
            if event.started_at < now and event.id != editable_event_id:
                grayed_out_event_ids.add(event.id)
                event.is_grayed_out = True
            else:
                event.is_grayed_out = False

        return events, editable_event_id, grayed_out_event_ids

    def get(self, request, username):
        # Get date range from query params or default to last 8 events
        event_limit = int(request.GET.get('event_limit') or 8)
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        # Fetch and organize events
        events, editable_event_id, grayed_out_event_ids = self._fetch_events(
            event_limit, start_date, end_date, include_prefetch=True
        )

        # Get all current members, ordered alphabetically for now
        members = Person.objects.filter(
            memberships__user=self.org_user,
            memberships__person__roles__id=Role.MEMBER
        ).distinct().order_by('last_name')

        # Get attendance types
        present_type = AttendanceType.objects.get(pk=AttendanceType.PRESENT)

        # Build attendance matrix
        dashboard_data = self._build_attendance_matrix(members, events, present_type)

        # Calculate totals per event
        event_totals = self._calculate_event_totals(events, members, present_type)

        context = {
            'org_user': self.org_user,
            'members': members,
            'events': events,
            'dashboard_data': dashboard_data,
            'event_totals': event_totals,
            'url_username': username,
        }

        return render(request, self.template_name, context)

    def post(self, request, username):
        """Handle bulk attendance updates."""
        with transaction.atomic():
            # Get all events and members being displayed
            event_limit = int(request.GET.get('event_limit') or 8)
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')

            # Fetch and organize events (no prefetch needed for POST)
            events, editable_event_id, grayed_out_event_ids = self._fetch_events(
                event_limit, start_date, end_date, include_prefetch=False
            )

            members = Person.objects.filter(
                memberships__user=self.org_user,
                memberships__person__roles__id=Role.MEMBER
            ).distinct()

            # Read submitted type IDs per cell
            VALID_TYPE_IDS = {
                AttendanceType.PRESENT,
                AttendanceType.WORK_SCHOOL,
                AttendanceType.ILLNESS,
                AttendanceType.PRIVATE_VACATION,
                AttendanceType.UNKNOWN,
            }
            submitted_types = {}
            for key, value in request.POST.items():
                if key.startswith('attendance_'):
                    parts = key.split('_')
                    if len(parts) == 3:
                        try:
                            submitted_types[(int(parts[1]), int(parts[2]))] = int(value)
                        except (ValueError, TypeError):
                            pass

            skipped_count = 0

            is_admin = AccessControl.can_add_event(
                request.user,
                self.org_user
            ).filter(person__roles__id=Role.ADMIN).exists()

            # Update all attendance records
            for event in events:
                # Skip if event is grayed out (past event, not the most recent)
                if event.id in grayed_out_event_ids:
                    skipped_count += members.count()
                    continue

                for member in members:
                    type_id = submitted_types.get((event.id, member.id), AttendanceType.UNKNOWN)
                    if type_id not in VALID_TYPE_IDS:
                        type_id = AttendanceType.UNKNOWN

                    # Get existing attendance if it exists
                    try:
                        attendance = Attendance.objects.get(event=event, person=member)
                        if attendance.attendance_type_id != type_id:
                            attendance.attendance_type_id = type_id
                            attendance.save()

                    except Attendance.DoesNotExist:
                        # Create new record
                        Attendance.objects.create(
                            event=event,
                            person=member,
                            attendance_type_id=type_id
                        )

                # NEW: Show appropriate success message
            if skipped_count > 0:
                messages.warning(
                    request,
                    f"Attendance updated! ({skipped_count} locked records were skipped)"
                )
            else:
                messages.success(request, "Attendance updated successfully!")

        # Redirect back to the same view with the same filters
        query_params = request.GET.urlencode()
        redirect_url = reverse('secondapp:attendance', kwargs={'username': username})
        if query_params:
            redirect_url += f'?{query_params}'
        return redirect(redirect_url)

    def _build_attendance_matrix(self, members, events, present_type):
        """Build efficient attendance lookup matrix."""
        # Create lookup dict: {event_id: {person_id: attendance_type_id}}
        attendance_lookup = {}
        for event in events:
            attendance_lookup[event.id] = {
                att.person_id: {
                    'type_id': att.attendance_type_id,
                    # 'is_locked': att.is_locked
                }
                for att in event.attendance_set.all()
            }

        # Build row data for each member
        dashboard_data = []
        for member in members:
            row = {
                'member': member,
                'attendance_cells': [],
                'total_present': 0,
                'total_events': 0,
            }

            # Build list of attendance cells in same order as events
            for event in events:
                att_data = attendance_lookup.get(event.id, {}).get(member.id, {})
                attendance_type_id = att_data.get('type_id')

                # Only count this event in the denominator if a record EXISTS
                if att_data:  # non-empty dict means a record exists in DB
                    row['total_events'] += 1

                # Check if this event is grayed out
                is_grayed_out = getattr(event, 'is_grayed_out', False)

                row['attendance_cells'].append({
                    'event_id': event.id,
                    'attendance_type_id': attendance_type_id,
                    'is_grayed_out': is_grayed_out,
                })

                if attendance_type_id == present_type.id:
                    row['total_present'] += 1

            row['percentage'] = (row['total_present'] / row['total_events'] * 100) if row['total_events'] > 0 else 0
            dashboard_data.append(row)

        return dashboard_data

    def _calculate_event_totals(self, events, members, present_type):
        """Calculate attendance totals per event."""
        from django.db.models import Count, Q

        total_members = members.count()

        # Build a dict of event_id -> present count using a single query
        event_ids = [e.id for e in events]
        present_counts = {}

        if event_ids:
            results = Attendance.objects.filter(
                event_id__in=event_ids,
                attendance_type=present_type
            ).values('event_id').annotate(count=Count('id'))

            for result in results:
                present_counts[result['event_id']] = result['count']

        # Return list in same order as events
        totals = []
        for event in events:
            present_count = present_counts.get(event.id, 0)
            totals.append({
                'event_id': event.id,
                'present': present_count,
                'total': total_members,
                'percentage': (present_count / total_members * 100) if total_members > 0 else 0
            })

        return totals



@method_decorator(login_required, name="dispatch")
class ImportDashboardView(View):
    template_name = 'secondapp/import_dashboard.html'

    VALID_METHODS = ["songs", "members", "events", "attendance", "event_songs"]


    def dispatch(self, request, *args, **kwargs):
        """Handle permission checking before processing the request."""
        url_username = self.kwargs.get("username")
        self.org_user = get_object_or_404(CustomUser, username=url_username)

        if request.user != self.org_user:
            has_permission = AccessControl.can_edit_event(
                request.user, self.org_user
            ).exists()

            if not has_permission:
                return HttpResponseForbidden("You don't have permission to view this dashboard.")

        # Validate the import method from URL
        self.import_method = self.kwargs.get('method')
        if self.import_method not in self.VALID_METHODS:
            return HttpResponseForbidden(f"Invalid import method: {self.import_method}")

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, username, method):
        """Render the import dashboard with the appropriate method."""
        context = {
            'import_method': self.import_method,
            'org_user': self.org_user,
            'url_username': username,
        }
        if self.import_method == 'members':
            context['skills'] = Skill.objects.all()
        return render(request, self.template_name, context)

    def post(self, request, username, method):
        """Handle file upload and import."""
        if 'file' not in request.FILES:
            messages.error(request, "No file uploaded")
            return redirect('secondapp:import_dashboard', username=username, method=method)

        uploaded_file = request.FILES['file']
        delimiter = request.POST.get('delimiter', ';')
        if delimiter == '\\t':  # Convert literal '\t' string to actual tab character
            delimiter = '\t'
        person_mode = request.POST.get('person_mode')

        try:
            # Save uploaded file temporarily
            import tempfile
            import os

            # Create a temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as tmp_file:
                # Write the uploaded content to temp file
                file_content = uploaded_file.read().decode('utf-8')
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name

            try:
                # Call the appropriate import function based on method
                if self.import_method == 'songs':
                    result = import_songs(self.org_user, request, tmp_file_path, delimiter)
                elif self.import_method == 'members':
                    result = import_persons(self.org_user, person_mode, request, tmp_file_path, delimiter)
                elif self.import_method == 'events':
                    result = import_events(self.org_user, request, tmp_file_path, delimiter)
                elif self.import_method == 'attendance':
                    result = import_attendance(self.org_user, request, tmp_file_path, delimiter)
                elif self.import_method == 'event_songs':
                    result = import_event_songs(self.org_user, request, tmp_file_path, delimiter)
                else:
                    messages.error(request, f"Invalid import method: {self.import_method}")
                    return redirect('secondapp:import_dashboard', username=username, method=method)

                # Check result if your import functions return a dict
                if isinstance(result, dict) and result.get('success'):
                    messages.success(
                        request,
                        f"Successfully imported {result.get('count', 0)} {self.import_method}"
                    )
                elif result:  # If function returns True or similar
                    messages.success(request, f"Successfully imported {self.import_method}")
                else:
                    messages.warning(request, "Import completed with some issues")

            finally:
                # Clean up: delete the temporary file
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)

        except Exception as e:
            messages.error(request, f"Error during import: {str(e)}")

        return redirect('secondapp:import_dashboard', username=username, method=method)


@method_decorator(login_required, name="dispatch")
class ImportHubView(View):
    template_name = 'secondapp/import_hub.html'

    def dispatch(self, request, *args, **kwargs):
        """Handle permission checking before processing the request."""
        username = self.kwargs.get("username")
        self.org_user = get_object_or_404(CustomUser, username=username)

        if request.user != self.org_user:
            has_permission = AccessControl.can_edit_event(
                request.user, self.org_user
            ).exists()

            if not has_permission:
                return HttpResponseForbidden("You don't have permission to view this page.")

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, username):
        context = {
            'org_user': self.org_user,
            'url_username': username,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name="dispatch")
class CombineProjectsView(View):

    def dispatch(self, request, *args, **kwargs):
        """Handle permission checking before processing the request."""
        username = self.kwargs.get("username")
        self.org_user = get_object_or_404(CustomUser, username=username)

        if request.user != self.org_user:
            has_permission = AccessControl.can_edit_event(
                request.user, self.org_user
            ).exists()

            if not has_permission:
                return HttpResponseForbidden("You don't have permission to perform this action.")

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, username):
        combine_event_projects(self.org_user, request)
        return redirect('secondapp:import_hub', username=username)

    def get(self, request, username):
        return redirect('secondapp:import_hub', username=username)


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'secondapp/project_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        url_username = self.kwargs.get('username')
        org_user = get_object_or_404(CustomUser, username=url_username)
        return (
            Project.objects
            .filter(user=org_user)
            .annotate(
                num_main_events=Count(
                    'events',
                    filter=Q(events__event_type_id__in=[
                        EventType.CONCERT,
                        EventType.PERFORMANCE,
                        EventType.RECORDING,
                    ])
                ),
                num_rehearsals=Count(
                    'events',
                    filter=Q(events__event_type_id=EventType.REHEARSAL)
                ),
            )
            .order_by('-end_date')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_username'] = self.kwargs.get('username')
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'secondapp/project_form.html'
    success_url = None

    def get_queryset(self):
        url_username = self.kwargs.get('username')
        org_user = get_object_or_404(CustomUser, username=url_username)
        return Project.objects.filter(user=org_user)

    def form_valid(self, form):
        url_username = self.kwargs.get('username')
        org_user = get_object_or_404(CustomUser, username=url_username)
        form.instance.user = org_user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('secondapp:project_update', kwargs={'username': self.kwargs.get('username'), 'pk': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        url_username = self.kwargs.get('username')
        org_user = get_object_or_404(CustomUser, username=url_username)
        kwargs['user'] = org_user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_username'] = self.kwargs.get('username')
        return context


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'secondapp/project_update.html'
    success_url = None

    def get_queryset(self):
        url_username = self.kwargs.get('username')
        org_user = get_object_or_404(CustomUser, username=url_username)
        return Project.objects.filter(user=org_user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        url_username = self.kwargs.get('username')
        org_user = get_object_or_404(CustomUser, username=url_username)
        kwargs['user'] = org_user
        return kwargs

    def get_success_url(self):
        return reverse('secondapp:project_detail', kwargs={'username': self.kwargs.get('username'), 'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        url_username = self.kwargs.get('username')
        org_user = get_object_or_404(CustomUser, username=url_username)
        project = self.object

        event_search_q = self.request.GET.get('event_q', '')
        song_search_q = self.request.GET.get('song_q', '')
        guest_search_q = self.request.GET.get('guest_q', '')

        context['url_username'] = url_username
        context['event_search_q'] = event_search_q
        context['add_event_form'] = AddEventToProjectForm(
            org_user=org_user,
            project=project,
            search_q=event_search_q,
        )
        context['song_search_q'] = song_search_q
        context['guest_search_q'] = guest_search_q
        context['add_song_form'] = AddSongToProjectForm(
            org_user=org_user,
            project=project,
            search_q=song_search_q,
        )
        context['add_guest_form'] = AddGuestToProjectForm(
            org_user=org_user,
            project=project,
            search_q=guest_search_q,
        )
        return context


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'secondapp/project_detail.html'
    context_object_name = 'project'

    def get_queryset(self):
        url_username = self.kwargs.get('username')
        org_user = get_object_or_404(CustomUser, username=url_username)
        return Project.objects.filter(user=org_user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_username'] = self.kwargs.get('username')
        project = self.object

        # Get events ordered by start date
        context['events'] = project.events.all().order_by('started_at')

        # Get songs
        context['songs'] = project.songs.all().order_by('title')

        # Get guests
        context['guests'] = project.guests.all().order_by('last_name', 'first_name')

        # Get members: those active at any point during project's date range
        url_username = self.kwargs.get('username')
        org_user = get_object_or_404(CustomUser, username=url_username)

        if project.start_date:
            reference_date = project.start_date
        else:
            reference_date = date.today()

        # Query: persons who have a membership period that overlaps with project date range
        # If project has no end_date, use today as the upper bound for the query
        end_date = project.end_date if project.end_date else date.today()

        members = Person.objects.filter(
            membership_period__user=org_user,
            membership_period__role_id=Role.MEMBER,
            membership_period__started_at__lte=end_date,
        ).filter(
            Q(membership_period__ended_at__gte=reference_date) |
            Q(membership_period__ended_at__isnull=True)
        ).distinct().order_by('last_name', 'first_name')

        context['members'] = members

        return context


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'secondapp/project_confirm_delete.html'
    success_url = None

    def get_queryset(self):
        url_username = self.kwargs.get('username')
        org_user = get_object_or_404(CustomUser, username=url_username)
        return Project.objects.filter(user=org_user)

    def get_success_url(self):
        return reverse('secondapp:project_list', kwargs={'username': self.kwargs.get('username')})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_username'] = self.kwargs.get('username')
        return context




def quick_add_rehearsal(request, username):
    """Quickly create a rehearsal event with all members marked as absent."""
    org_user = get_object_or_404(CustomUser, username=username)

    # Check permissions
    if request.user != org_user:
        if not AccessControl.can_edit_event(request.user, org_user).exists():
            return HttpResponseForbidden("No permission")

    with transaction.atomic():
        # Get or create "Rehearsal" event type
        rehearsal_type, _ = EventType.objects.get_or_create(
            name='Rehearsal',
        )

        # Create event
        event = Event.objects.create(
            user=org_user,
            name=f"Rehearsal - {timezone.now().strftime('%B %d, %Y')}",
            event_type=rehearsal_type,
            started_at=timezone.now(),
            ended_at=timezone.now() + timedelta(hours=3),
            location="usual"
        )

        # Get all current members
        members = Person.objects.filter(
            memberships__user=org_user,
            memberships__person__roles__id=Role.MEMBER
        ).distinct()

        # Get the "Unknown" attendance type
        unknown_type = AttendanceType.objects.get(pk=AttendanceType.UNKNOWN)

        # Create attendance records for all members (default: unknown)
        attendance_records = [
            Attendance(
                event=event,
                person=member,
                attendance_type=unknown_type
            )
            for member in members
        ]
        Attendance.objects.bulk_create(attendance_records)

        messages.success(request, f"Rehearsal created with {len(attendance_records)} members!")

    # Redirect back to dashboard
    return redirect('secondapp:attendance', username=username)


def update_attendance_from_event_detail(request, attendance_id):
    attendance = get_object_or_404(Attendance, id=attendance_id)

    # Update attendance
    attendance.status = request.POST.get('status')
    # attendance.is_locked = True  # Lock this record
    # attendance.locked_reason = "Modified in event details"
    # attendance.last_modified_by = request.user
    attendance.save()

    return redirect('event_detail', event_id=attendance.event.id)





# @method_decorator(login_required, name='dispatch')
# class AttendanceCreateView(CreateView):
#     """Create attendance record for an event"""
#     model = Attendance
#     fields = ['person', 'status', 'notes']
#     template_name = 'secondapp/attendance_form.html'
#
#     def dispatch(self, request, *args, **kwargs):
#         url_username = self.kwargs.get("username")
#         self.event = get_object_or_404(Event, pk=self.kwargs["event_pk"])
#
#         if url_username:
#             self.customuser = get_object_or_404(
#                 CustomUser,
#                 username=url_username
#             )
#             # Check permission
#             if request.user != self.customuser:
#                 if not AccessControl.can_edit_event(request.user, self.customuser).exists():
#                     return HttpResponseForbidden()
#         else:
#             self.customuser = request.user
#
#         return super().dispatch(request, *args, **kwargs)
#
#     def form_valid(self, form):
#         form.instance.event = self.event
#         return super().form_valid(form)
#
#     def get_success_url(self):
#         return reverse_lazy('secondapp:event_detail', kwargs={
#             'username': self.kwargs['username'],
#             'pk': self.event.pk
#         })
#
#
# @method_decorator(login_required, name='dispatch')
# class AttendanceListView(ListView):
#     """List all attendance records for an event"""
#     model = Attendance
#     template_name = 'secondapp/attendance_list.html'
#     context_object_name = 'attendances'
#
#     def dispatch(self, request, *args, **kwargs):
#         url_username = self.kwargs.get("username")
#         self.event = get_object_or_404(Event, pk=self.kwargs["event_pk"])
#
#         if url_username:
#             self.customuser = get_object_or_404(
#                 CustomUser,
#                 username=url_username
#             )
#             # Check permission
#             if request.user != self.customuser:
#                 if not AccessControl.can_view_event(request.user, self.customuser).exists():
#                     return HttpResponseForbidden()
#         else:
#             self.customuser = request.user
#
#         return super().dispatch(request, *args, **kwargs)
#
#     def get_queryset(self):
#         return Attendance.objects.filter(event=self.event).select_related('person', 'event')
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['event'] = self.event
#         context['customuser'] = self.customuser
#         return context
#
#
# @method_decorator(login_required, name='dispatch')
# class AttendanceUpdateView(UpdateView):
#     """Edit attendance record"""
#     model = Attendance
#     fields = ['person', 'status', 'notes']
#     template_name = 'secondapp/attendance_form.html'
#
#     def dispatch(self, request, *args, **kwargs):
#         url_username = self.kwargs.get("username")
#
#         if url_username:
#             self.customuser = get_object_or_404(
#                 CustomUser,
#                 username=url_username
#             )
#             # Check permission
#             if request.user != self.customuser:
#                 if not AccessControl.can_edit_event(request.user, self.customuser).exists():
#                     return HttpResponseForbidden()
#         else:
#             self.customuser = request.user
#
#         return super().dispatch(request, *args, **kwargs)
#
#     def get_queryset(self):
#         return Attendance.objects.filter(event__user=self.customuser)
#
#     def get_success_url(self):
#         return reverse_lazy('secondapp:event_detail', kwargs={
#             'username': self.kwargs['username'],
#             'pk': self.object.event.pk
#         })
# ===================================================================================
# -----------------------------------------------------
# class IndexView(generic.ListView): #BreadcrumbMixin,
#     model = Rehearsal
#     template_name = "secondapp/index.html"
#     context_object_name = "rehearsal_list"
#     queryset = Rehearsal.objects.filter(is_cancelled=False).order_by('-calendar')[:20]
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         now = timezone.now()
#         paginated_rehearsals = context["rehearsal_list"]
#
#         context["upcoming_rehearsals"] = [
#             rehearsal for rehearsal in paginated_rehearsals
#             if rehearsal.calendar > now
#         ]
#         context["past_rehearsals"] = [
#             rehearsal for rehearsal in paginated_rehearsals
#             if rehearsal.calendar < now
#         ]
#
#         for rehearsal in context['upcoming_rehearsals']:
#             rehearsal.member_status = rehearsal.get_member_status()
#
#         for rehearsal in context['past_rehearsals']:
#             rehearsal.member_status = rehearsal.get_member_status()
#
#         happening_now = Rehearsal.objects.filter(
#             is_canceled=False,
#             calendar__gte=now - timedelta(minutes=660),
#             calendar__lte=now + timedelta(minutes=660)
#         ).first()
#
#         context['happening_now'] = happening_now
#         return context
#
#
# # ---------------------------------------
# class RehearsalListView(BreadcrumbMixin, generic.ListView):
#     template_name = "secondapp/rehearsal_list.html"
#     context_object_name = "rehearsal_list"
#     paginate_by = 20
#     section_name = "rehearsal"
#     page_name = "list"
#
#     def get_queryset(self):
#         return Rehearsal.objects.filter(is_cancelled=False).order_by("-calendar")
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         now = timezone.now()
#
#         paginated_rehearsals = context['rehearsal_list']
#         context['upcoming_rehearsals'] = [
#             rehearsal for rehearsal in paginated_rehearsals
#             if rehearsal.calendar >= now
#         ]
#         context['past_rehearsals'] = [
#             rehearsal for rehearsal in paginated_rehearsals
#             if rehearsal.calendar < now
#         ]
#
#         for rehearsal in context['upcoming_rehearsals']:
#             rehearsal.member_status = rehearsal.get_member_status()
#
#         for rehearsal in context['past_rehearsals']:
#             rehearsal.member_status = rehearsal.get_member_status()
#
#         happening_now = Rehearsal.objects.filter(
#             is_canceled=False,
#             calendar__gte=now - timedelta(minutes=660),
#             calendar__lte=now + timedelta(minutes=660)
#         ).first()
#
#         context['happening_now'] = happening_now
#
#         return context
#
#
# class RehearsalDetailView(BreadcrumbMixin, generic.DetailView):
#     model = Rehearsal
#     template_name = "secondapp/rehearsal_detail.html"
#     section_name = "rehearsal"
#     page_name = "detail"
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         rehearsal = self.object
#         now = timezone.now()
#         member_status = rehearsal.get_member_status()
#         context.update(member_status)
#
#         return context
#
#
# class RehearsalCreateView(BreadcrumbMixin, generic.CreateView):
#     model = Rehearsal
#     form_class = RehearsalForm
#     template_name = "secondapp/rehearsal_form.html"
#     section_name = "rehearsal"
#     page_name = "new"
#
# #    def form_valid(self, form):
# #        rehearsal = form.save()
#
# #        for field_name, value in form.cleaned_data.items():
# #            if field_name.startswith('member_') and value:
# #                member_id = field_name.split('_')[1]
# #                rehearsal.members.add(member_id)
#
# #        return super().form_valid(form)
#
#     def get_success_url(self):
#         return reverse_lazy("secondapp:rehearsal_detail", kwargs={"pk": self.object.pk})
#
#
# class RehearsalUpdateView(BreadcrumbMixin, generic.UpdateView):
#     model = Rehearsal
#     form_class = RehearsalForm
#     template_name = "secondapp/rehearsal_form.html"
#     section_name = "rehearsal"
#     page_name = "update"
#
# #    def form_valid(self, form):
# #        rehearsal = form.save()
#
# #        rehearsal.members.clear()
# #        for field_name, value in form.cleaned_data.items():
# #            if field_name.startswith('member_') and value:
# #                member_id = field_name.split('_')[1]
# #                rehearsal.members.add(member_id)
#
# #        return super().form_valid(form)
#
#     def get_success_url(self):
#         return reverse_lazy("secondapp:rehearsal_detail", kwargs={"pk": self.object.pk})
#
#
# class RehearsalDeleteView(BreadcrumbMixin, generic.DeleteView):
#     model = Rehearsal
#     template_name = "secondapp/rehearsal_confirm.html"
#     section_name = "rehearsal"
#     page_name = "delete"
#
#     def get_success_url(self):
#         return reverse_lazy("secondapp:rehearsal_list")
#
#
#
# # -------------------------------------------
# class SongListView(BreadcrumbMixin, generic.ListView):
#     model = Song
#     template_name = "secondapp/song_list.html"
#     context_object_name = "song_list"
#     section_name = "song"
#     page_name = "list"
#
#     def get_queryset(self):
#         queryset = Song.objects.all()
#         # Get the sort_by parameter
#         sort_by = self.request.GET.get('sort_by', None)
#
#         search_query = self.request.GET.get("search")
#         if search_query:
#             queryset = queryset.filter(
#                 Q(title__icontains=search_query) |
#                 Q(composer__last_name__icontains=search_query)
#             )
#         if sort_by:
#             if sort_by == 'title_A':
#                 queryset = queryset.order_by('title')
#             elif sort_by == "title_Z":
#                 queryset = queryset.order_by("-title")
#             elif sort_by == 'composer_A':
#                 queryset = queryset.order_by('composer__last_name', 'composer__first_name')
#             elif sort_by == "composer_Z":
#                 queryset = queryset.order_by("-composer__last_name", "composer__first_name")
#             elif sort_by == "ID_first":
#                 queryset = queryset.order_by("pk")
#             elif sort_by == "ID_last":
#                 queryset = queryset.order_by("-pk")
#             elif sort_by == "copies_A":
#                 queryset = queryset.order_by("copies")
#             elif sort_by == "copies_Z":
#                 queryset = queryset.order_by("-copies")
#
#         return queryset
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["search_query"] = self.request.GET.get("search", "")
#         return context
#
#
# class SongDetailView(BreadcrumbMixin, generic.DetailView):
#     model = Song
#     template_name = "secondapp/song_detail.html"
#     context_object_name = "song"
#     section_name = "song"
#     page_name = "detail"
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["recent_rehearsals"] = self.object.rehearsals.all()
#
#         return context
#
#
# class SongCreateView(BreadcrumbMixin, generic.CreateView):
#     model = Song
#     form_class = SongForm
#     template_name = "secondapp/song_form.html"
#     section_name = "song"
#     page_name = "new"
#
#     def get_success_url(self):
#         return reverse_lazy("secondapp:song_detail", kwargs={"pk": self.object.pk})
#
#
# class SongUpdateView(BreadcrumbMixin, generic.UpdateView):
#     model = Song
#     form_class = SongForm
#     template_name = "secondapp/song_form.html"
#     section_name = "song"
#     page_name = "update"
#
#     def get_success_url(self):
#         return reverse_lazy("secondapp:song_detail", kwargs={"pk": self.object.pk})
#
#
# class SongDeleteView(BreadcrumbMixin, generic.DeleteView):
#     model = Song
#     template_name = "secondapp/song_confirm_delete.html"
#     section_name = "song"
#     page_name = "delete"
#
#     def get_success_url(self):
#         return reverse_lazy("secondapp:song_list")
#
#
# ----------------------------------------
# class TagListAndCreateView(TagListAndCreateMixin, View):
#     section_name = "tag"
#     pass
#
#
# # ---------------------------------------------------------
# class PersonListView(PersonRoleMixin, BreadcrumbMixin, ListView):
#     template_name = "secondapp/person_list.html"
#     context_object_name = "people"
#     page_name = "list"
#
#     def get_section_name(self):
#         return self.kwargs.get("role")
#
#     def get_breadcrumbs(self):
#         self.section_name = self.get_section_name()
#         return super().get_breadcrumbs()
#
#     def get_base_queryset(self):
#         model = self.get_model()
#         queryset = model.objects.all().order_by("last_name")
#
#         search_query = self.request.GET.get("search")
#         if search_query:
#             queryset = queryset.filter(
#                 Q(first_name__icontains=search_query) |
#                 Q(last_name__icontains=search_query)
#             )
#         return queryset
#
#     def get_queryset(self):
#         queryset = self.get_base_queryset
#         model = self.get_model()
#
#         if hasattr(model, "is_active"):
#             return queryset
#
#         return queryset
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         base_queryset = self.get_base_queryset()
#         model = self.get_model()
#
#         if hasattr(model, 'is_active'):
#             context["active_people"] = base_queryset.filter(is_active=True)
#             context["inactive_people"] = base_queryset.filter(is_active=False)
#             context["has_voice"] = True
#
#             all_rehearsals = Rehearsal.objects.filter(is_cancelled=False).count()
#             for person in context["active_people"]:
#                 attendance = person.get_rehearsal_attendance()
#                 person.missing_count = attendance["missing"].count()
#                 person.total_rehearsals = all_rehearsals
#
#             for person in context["inactive_people"]:
#                 attendance = person.get_rehearsal_attendance()
#                 person.missing_count = attendance["missing"].count()
#                 person.total_rehearsals = all_rehearsals
#
#         else:
#             context["active_people"] = base_queryset
#             context["inactive_people"] = base_queryset.none()
#             context["has_voice"] = False
#
#         context["search_query"] = self.request.GET.get("search", "")
#
#         return context
#
#
# class PersonDetailView(PersonRoleMixin, BreadcrumbMixin, DetailView):
#     template_name = 'secondapp/person_detail.html'
#     context_object_name = 'person'
#     page_name = "detail"
#
#     def get_section_name(self):
#         return self.kwargs.get("role")
#
#     def get_breadcrumbs(self):
#         self.section_name = self.get_section_name()
#         return super().get_breadcrumbs()
#
#     def get_object(self, queryset=None):
#         return self.get_model().objects.get(pk=self.kwargs.get('pk'))
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         person = self.object
#
#         if hasattr(person, "song"):
#             context["song"] = self.object.song.all()
#         else:
#             context["song"] = []
#
#         if isinstance(person, Member):
#             attendance = person.get_rehearsal_attendance()
#             context.update(attendance)
#
#         if hasattr(person, "activity"):
#             context["activity"] = person.activity.all()
#         else:
#             context["activity"] = []
#
#         return context
#
#
# class PersonCreateView(PersonRoleMixin, BreadcrumbMixin, CreateView):
#     template_name = "secondapp/person_form.html"
#     page_name = "new"
#
#     def get_section_name(self):
#         return self.kwargs.get("role")
#
#     def get_breadcrumbs(self):
#         self.section_name = self.get_section_name()
#         return super().get_breadcrumbs()
#
#     def get_success_url(self):
#         return reverse_lazy("secondapp:person_detail", kwargs={"role": self.kwargs.get('role'), "pk": self.object.pk})
#
#
# class PersonUpdateView(PersonRoleMixin, BreadcrumbMixin, UpdateView):
#     template_name = "secondapp/person_form.html"
#     context_object_name = "person"
#     page_name = "update"
#
#     def get_section_name(self):
#         return self.kwargs.get("role")
#
#     def get_breadcrumbs(self):
#         self.section_name = self.get_section_name()
#         return super().get_breadcrumbs()
#
#     def get_object(self, queryset = None):
#         return self.get_model().objects.get(pk=self.kwargs.get("pk"))
#
#     def get_success_url(self):
#         return reverse_lazy(
#             "secondapp:person_detail",
#             kwargs={
#                 "role": self.kwargs.get('role'),
#                 "pk": self.object.pk
#             }
#         )
#
#
# class PersonDeleteView(PersonRoleMixin, BreadcrumbMixin, DeleteView):
#     model = "person"
#     template_name = 'secondapp/person_confirm_delete.html'
#     context_object_name = "person"
#     page_name = "delete"
#
#     def get_section_name(self):
#         return self.kwargs.get("role")
#
#     def get_breadcrumbs(self):
#         self.section_name = self.get_section_name()
#         return super().get_breadcrumbs()
#
#     def dispatch(self, request, *args, **kwargs):
#         self.model = self.get_model()
#         return super().dispatch(request, *args, **kwargs)
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["role"] = self.kwargs.get("role")
#         return context
#
#     def get_object(self, queryset = None):
#         model = self.get_model()
#         pk = self.kwargs.get("pk")
#         try:
#             return model.objects.get(pk=pk)
#         except model.DoesNotExist:
#             raise Http404(f"{model.__name__} with id {pk} does not exist")
#
#     def post(self, request, *args, **kwargs):
#         return self.delete(request, *args, **kwargs)
#
#     def delete(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         success_url = self.get_success_url()
#
#         self.object.delete()
#
#         #from django.http import HttpResponseRedirect
#         return HttpResponseRedirect(success_url)
#
#     def get_success_url(self):
#         role = self.kwargs.get("role")
#         return reverse_lazy("secondapp:person_list", kwargs={"role": role})
#
#
# # ---------------------------------------------
#
# class EnsembleListView(BreadcrumbMixin, generic.ListView):
#     model = Ensemble
#     template_name = "secondapp/ensemble_list.html"
#     context_object_name = "ensemble_list"
#     section_name = "ensemble"
#     page_name = "list"
#
#
# class EnsembleDetailView(BreadcrumbMixin, generic.DetailView):
#     model = Ensemble
#     template_name = "secondapp/ensemble_detail.html"
#     context_object_name = "ensemble"
#     section_name = "ensemble"
#     page_name = "detail"
#
# class EnsembleCreateView(BreadcrumbMixin, generic.CreateView):
#     model = Ensemble
#     form_class = EnsembleForm
#     template_name = "secondapp/ensemble_form.html"
#     section_name = "ensemble"
#     page_name = "new"
#
#     def get_success_url(self):
#         return reverse_lazy("secondapp:ensemble_detail", kwargs={"pk": self.object.pk})
#
#
# class EnsembleUpdateView(BreadcrumbMixin, generic.UpdateView):
#     model = Ensemble
#     form_class = EnsembleForm
#     template_name = "secondapp/ensemble_form.html"
#     section_name = "ensemble"
#     page_name = "update"
#
#     def get_success_url(self):
#         return reverse_lazy("secondapp:ensemble_detail", kwargs={"pk": self.object.pk})
#
#
# class EnsembleDeleteView(BreadcrumbMixin, generic.DeleteView):
#     model = Ensemble
#     template_name = "secondapp/ensemble_confirm_delete.html"
#     section_name = "ensemble"
#     page_name = "delete"
#
#     def get_success_url(self):
#         return reverse_lazy("secondapp:ensemble_list")
#
# # ---------------------------------------------
#
# class ActivityCreateView(BreadcrumbMixin, generic.CreateView):
#     model = Activity
#     fields = ["start_date", "end_date", "ensemble"]
#     template_name = "secondapp/activity_form.html"
#     section_name = "activity"
#     page_name = "new"
#
#     def form_valid(self, form):
#         role = self.kwargs["role"]
#         person_id = self.kwargs["pk"]
#
#         if role == "member":
#             form.instance.member = Member.objects.get(pk=person_id)
#         elif role == "conductor":
#             form.instance.conductor = Conductor.objects.get(pk=person_id)
#
#         return super().form_valid(form)
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["role"] = self.kwargs["role"]
#         person_id = self.kwargs["pk"]
#         if context["role"] == "member":
#             context["person"] = Member.objects.get(pk=person_id)
#         elif context["role"] == "conductor":
#             context["person"] = Conductor.objects.get(pk=person_id)
#
#         return context
#
#     def get_success_url(self):
#         return self.object.get_absolute_url()
#
# class ActivityUpdateView(BreadcrumbMixin, generic.UpdateView):
#     model = Activity
#     fields = ["start_date", "end_date", "ensemble"]
#     template_name = "secondapp/activity_form.html"
#     section_name = "activity"
#     page_name = "update"
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         if self.object.member:
#             context["person"] = self.object.member
#             context["role"] = "member"
#         elif self.object.conductor:
#             context["person"] = self.object.conductor
#             context["role"] = "conductor"
#         return context
#
#     def get_success_url(self):
#         return self.object.get_absolute_url()
#
#
# class ActivityDeleteView(BreadcrumbMixin, generic.DeleteView):
#     model = Activity
#     template_name = "secondapp/activity_confirm_delete.html"
#     section_name = "activity"
#     page_name = "delete"
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         if self.object.member:
#             context["person"] = self.object.member
#             context["role"] = "member"
#         elif self.object.conductor:
#             context["person"] = self.object.conductor
#             context["role"] = "conductor"
#         return context
#
#     def get_success_url(self):
#         if self.object.member:
#             return self.object.member.get_absolute_url()
#         elif self.object.conductor:
#             return self.object.conductor.get_absolute_url()
#         return "/"
#
# #---------------------------------------------------------
#
# class ImportFileListView(generic.ListView):
#     model = ImportFile
#     template_name = "secondapp/import_list.html"
#     context_object_name = "import_list"
#     section_name = "import"
#
#
# def import_members(reader):
#     conductor, _ = Conductor.objects.get_or_create(role="Conductor", defaults={"first_name": "Branka"})
#     ensemble, _ = Ensemble.objects.update_or_create(name="De profundis", address="address")
#
#     for row in reader:
#         name_together = {"first_name": row["Ime"], "last_name": row["Priimek"]}
#         addr_together = {"address": row["Naslov"],
#                          "email": row["e-pošta"],
#                          "phone_number": row["Telefon"],
#                          "mobile_number": row["Mobilc"]}
#         raw_date = row["Datum roj."].strip()
#         invalid_date = {"0000-00-00", "00.00.0000", "00. 00. 0000"}
#         bday = {"birth_date": None if not raw_date or raw_date in invalid_date
#                   else datetime.strptime(raw_date, "%d. %m. %Y").date()}
#         glas = row["Glas"]
#         if glas == "Alt":
#             voice_dict = {"voice": "Alto"}
#         elif glas == "Sopran":
#             voice_dict = {"voice": "Soprano"}
#         elif glas == "Tenor":
#             voice_dict = {"voice": "Tenor"}
#         elif glas == "Bas":
#             voice_dict = {"voice": "Bass"}
#         else:
#             voice_dict = {}
#
#         right_now = {"is_active": False}
#         if "Aktiven" in row:
#             date_range = row["Aktiven"].split(",")
#             trajanje = []
#
#             for obdobje in date_range:
#                 if not obdobje or "-" not in obdobje:
#                     continue
#
#                 seznam = obdobje.split("-")
#                 if len(seznam) < 3:
#                     continue
#                 beginning = None
#                 finish = None
#
#                 if seznam[0] and seznam[1] and seznam[2]:
#                     try:
#                         beginning = date(int(seznam[0]), int(seznam[1]), int(seznam[2]))
#                     except ValueError:
#                         beginning = None
#
#                 if len(seznam) >= 6 and seznam[3] and seznam[4] and seznam[5]:
#                     try:
#                         finish = date(int(seznam[3]), int(seznam[4]), int(seznam[5]))
#                     except ValueError:
#                         finish = None
#                 trajanje.append((beginning, finish))
#
#                 if beginning is not None and finish is not None:
#                     continue
#                 elif beginning is None and finish is None:
#                     continue
#                 else:
#                     right_now = {"is_active": True}
#
#         date_active = ", ".join([f"{a} - {b}" for a, b in trajanje])   # this is only backup text field in member.date_active
#
#         member_data = {**name_together, **addr_together, **bday, **right_now}
#
#         if not voice_dict:
#             member_data.update({"role":"Conductor"})
#             conductor.first_name = member_data.get("first_name", conductor.first_name)
#             conductor.last_name = member_data["last_name"]
#             conductor.address = member_data["address"]
#             conductor.email = member_data["email"]
#             conductor.mobile_number = member_data["mobile_number"]
#             conductor.birth_date = member_data["birth_date"]
#
#             conductor.save()
#         else:
#             member_data.update({"date_active":date_active, **voice_dict, "role":"Member"})
#             member_obj, _ = Member.objects.update_or_create(
#                 first_name=member_data["first_name"],
#                 last_name=member_data["last_name"],
#                 defaults=member_data)
#             for aaaaa, bbbbb in trajanje:
#                 existing_activity = Activity.objects.filter(
#                     conductor = conductor,
#                     ensemble = ensemble,
#                     member = member_obj,
#                     start_date = aaaaa,
#                     end_date = bbbbb
#                 ).first()
#                 if not existing_activity:
#                     Activity.objects.create(
#                         conductor=conductor,
#                         ensemble=ensemble,
#                         member=member_obj,
#                         start_date=aaaaa,
#                         end_date=bbbbb,
#                     )
#
#
# def import_songs(reader):
#
#     group_map = {"0":"mixed", "1":"female", "2":"male"}
#     for row in reader:
#
#         composer_name = {"last_name": row["Skladatelj priimek"].strip(),
#                          "first_name":row["Skladatelj ime"].strip()}
#         composer = None
#         if any(composer_name.values()):
#             composer, _ = Composer.objects.update_or_create(**composer_name, defaults={"role": "Composer"})
#
#         poet_name = {"last_name": row["Tekstopisec priimek"].strip(),
#                      "first_name": row["Tekstopisec ime"].strip()}
#         poet = None
#         if any(poet_name.values()):
#             poet, _ = Poet.objects.update_or_create(**poet_name, defaults={"role": "Poet"})
#
#         song_identity = {#"id":row["ID"],
#                          "title": row["Naslov"],
#                          "year": int(row["Leto"]) if row["Leto"].strip() else None,
#                          "number_of_voices": int(row["Št. glasov"]) if row["Št. glasov"].strip() else None,
#                          "number_of_pages": int(row["Št. strani"]) if row["Št. strani"].strip() else None,
#                          "number_of_copies": int(row["Št. kopij"]) if row["Št. kopij"].strip() else None,
#                          "additional_notes": row["Opombe"].strip() or None
#                          }
#
#
#         group_type = group_map.get(str(row["Zasedba"]))
#         song_identity.update({"group": group_type,
#                               "composer": composer,
#                               "poet": poet})
#         Song.objects.update_or_create(
#             id=int(row["ID"]),
#             defaults=song_identity
#         )
#
#
# class ImportFileFormView(generic.FormView):
#     form_class = ImportFileForm
#     model = ImportFile
#     template_name = "secondapp/import_upload.html"
#     success_url = reverse_lazy("secondapp:import_detail")
#     section_name = "import"
#
#     def form_valid(self, form):
#         import_mode = form.cleaned_data["import_mode"]
#         uploaded_file = self.request.FILES["file"]
#
#         # TEST # -----  detected encoding: Windows-1250 ##################  cp1250   utf-8
#         lines = uploaded_file.read().decode("utf-8").splitlines()
#         reader = csv.DictReader(lines, delimiter=',')
#
#         if import_mode == "members":
#             import_members(reader)
#
#         elif import_mode == "songs":
#             import_songs(reader)
#
#
#         uploaded_file.close()
#
#         return super().form_valid(form)
#
#     def get_success_url(self):
#         return reverse_lazy("secondapp:import_list")
#
#
# class ImportFileDetailView(generic.DetailView):
#     model = ImportFile
#     template_name = "secondapp/import_detail.html"
#     context_object_name = "import_detail"
#    section_name = "import"