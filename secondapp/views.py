import csv
from dataclasses import field
from fileinput import filename
import sqlite3

from django.contrib.auth import logout
from django.shortcuts import redirect
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import PermissionDenied
from django.db import connection
from django.http import HttpRequest, HttpResponse, Http404, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.template.context_processors import request
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.sessions.models import Session
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.views import generic
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View, FormView, TemplateView
from django.views.generic.edit import DeleteView
from django.db.models import Q, Prefetch
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
from .forms import OrgMemberForm
from .models import Organization, Person, Membership, MembershipPeriod, Role, PersonSkill, PersonQuerySet

# from .forms import RehearsalForm, Member, ComposerForm, PoetForm, ArrangerForm, MusicianForm, SongForm, TagForm, PersonForm, EnsembleForm, ActivityForm, ImportFileForm
# from .models import Rehearsal, Member, Composer, Poet, Arranger, Musician, Song, Ensemble, Activity, Conductor, ImportFile
# from .mixins import TagListAndCreateMixin, PersonRoleMixin, BreadcrumbMixin, LoginRequiredMixin

from .models import CustomUser, Organization, Person, Membership, Role, Song, Skill
from .forms import RegisterForm, OrganizationForm, PersonForm, SongForm, SkillForm
from .forms import CustomUserCreationForm
from .mixins import RoleRequiredMixin, SkillListAndCreateMixin


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

    def get_object(self, queryset=None):
        return Person.objects.get(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        user = self.request.user
        organization = getattr(user, "organization", None)
        user_role = getattr(user, "role", None)

        if self.object.user:
            self.object.user.email = self.object.email
            self.object.user.save()

        # Admin can make new persons
        if organization and user_role == Role.ADMIN:
            self.object.user = None
            self.object.save()
            Membership.objects.create(
                organization=self.organization,
                person=self.object,
                role=Role.MEMBER,
                is_active=True
            )
        else:
            # non-admin access
            self.object.user = self.request.user
            self.object.save()

        return redirect(self.get_success_url())


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "secondapp/index2.html"
    model = Person

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["memberships"] = Membership.objects.filter(person__user=user).select_related("organization")
        return context


@method_decorator(login_required, name='dispatch')
class OrganizationDashboard(TemplateView):
    """Home page for specific organizations."""
    template_name = "secondapp/org_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        username = self.kwargs["username"]
        organization = get_object_or_404(
            Organization,
            user__username=username
        )

        context["organization"] = organization
        context["memberships"] = Membership.objects.filter(
            organization=organization
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
            person = Person.objects.filter(user=self.request.user).first()

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

            # create first admin person of the org
            person_admin = Person.objects.create(
                owner=person,
                email=person.email,
                first_name=person.first_name,
                last_name=person.last_name,
            )

            Membership.objects.create(
                organization=organization,
                person=person_admin,
                role_id=Role.ADMIN,
                is_active=True,
            )

        return super().form_valid(form)


class OrgMemberMixin(RoleRequiredMixin):
    """Mixin for organization member views."""
    allowed_roles = [Role.ADMIN, Role.MEMBER]

    def dispatch(self, request, *args, **kwargs):
        # Get username from URL
        username = self.kwargs.get("username")

        # Find the organization
        self.organization = get_object_or_404(Organization, user__username=username)

        # Get the user's Person
        person = request.user.persons.first()

        # Get the user's role in this organization
        self.user_role = self.organization.get_role(request.user)
        if not self.role_allowed(self.user_role):
            raise PermissionDenied(f"Your role '{self.user_role}' does not have access.")

        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class OrgMemberListView(OrgMemberMixin, TemplateView):
    """Shows all members of an organization."""
    template_name = "secondapp/org_member_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        memberships_specific = Membership.objects.filter(
            organization=self.organization,
            is_active=True
        ).select_related("person").prefetch_related("person__roles", "person__skills").order_by("person__last_name")

        # remove double lines
        seen = set()
        unique_memberships = []
        for m in memberships_specific:
            if m.person.id not in seen:
                unique_memberships.append(m)
                seen.add(m.person.id)

        context["memberships"] = unique_memberships
        return context


@method_decorator(login_required, name='dispatch')
class OrgMemberAddView(OrgMemberMixin, FormView):
    """Add new member."""
    template_name = "secondapp/org_member_form.html"
    form_class = OrgMemberForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["organization"] = self.organization
        context["page_title"] = f"Add Member to {self.organization.name}"
        return context

    def form_valid(self, form):
        person_data = form.get_person_data()

        with transaction.atomic():
            # find or create Person
            person = Person.objects.filter(
                email=person_data["email"],
                memberships__organization=self.organization
            ).first()

            if not person:
                person = Person.objects.create(**person_data, user=None)
            else: # update existing person
                for field, value in person_data.items():
                    if field != "email":  # don't update email
                        setattr(person, field, value)
                person.save()

            # create memberships for selected roles
            for role_name, is_active in form.get_selected_roles():
                membership, created = Membership.objects.get_or_create(
                    organization=self.organization,
                    person=person,
                    role=role_name,
                    defaults={"is_active": is_active}
                )

                if created:
                    MembershipPeriod.objects.create(membership=membership)
                else:
                    membership.is_active = is_active
                    membership.save()

            for skill in form.get_selected_skills():
                PersonSkill.objects.update_or_create(
                    person=person,
                    skill=skill
                )

        return redirect("secondapp:org_member_list", username=self.kwargs["username"])


@method_decorator(login_required, name='dispatch')
class OrgMemberEditView(OrgMemberMixin, FormView):
    """Edit existing member."""
    template_name = "secondapp/org_member_form.html"
    form_class = OrgMemberForm


    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        username = self.kwargs.get("username")
        self.organization = Organization.objects.get(user__username=username)

        self.person = get_object_or_404(
            Person.objects.prefetch_related(
                Prefetch(
                    "memberships",
                    queryset=Membership.objects.filter(
                        organization=self.organization
                    )
                )
            ),
            pk=self.kwargs["pk"]
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # pre-fill if this is a GET request
        if self.request.method == "GET":
            # grab existing memberships
            memberships = Membership.objects.filter(
                organization=self.organization,
                person=self.person,
            )
            skills = PersonSkill.objects.filter(person=self.person)

            # dict of the checkboxes
            initial = {
                # person info
                "first_name": self.person.first_name,
                "last_name": self.person.last_name,
                "email": self.person.email,
                "phone": self.person.phone,
                "address": self.person.address,
                # checkboxes start as False
                "role_admin": False,
                "role_member": False,
                "role_supporter": False,
                "active_admin": False,
                "active_member": False,
                "active_supporter": False,
                "skills": self.person.person_skill.values_list("skill", flat=True),
            }

            for m in memberships: # check the right boxes
                role = m.role.title.lower()  # "ADMIN" == "admin"
                initial[f"role_{role}"] = True
                initial[f"active_{role}"] = m.is_active

            form.initial = initial

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.organization
        context["page_title"] = f"Edit {self.person.first_name} {self.person.last_name}"
        return context

    def form_valid(self, form):
        person_data = form.get_person_data()

        with transaction.atomic():
            # update person (exclude email)
            for field, value in person_data.items():
                if field != "email":
                    setattr(self.person, field, value)
            self.person.save()

            # get all selected roles from form
            selected_roles = {role_name: is_active for role_name, is_active in form.get_selected_roles()}

            # handle each possible role
            for role_name in [Role.ADMIN, Role.MEMBER, Role.SUPPORTER, Role.EXTERNAL]:
                membership = Membership.objects.filter(
                    organization=self.organization,
                    person=self.person,
                    role=role_name,
                ).first()

                if role_name in selected_roles:
                    # role is checked
                    is_active = selected_roles[role_name]

                    if not membership:
                        # new role
                        membership = Membership.objects.create(
                            organization=self.organization,
                            person=self.person,
                            role=role_name,
                            is_active=is_active,
                        )
                        MembershipPeriod.objects.create(membership=membership)
                    else:
                        # existing role, check if activity changed
                        if membership.is_active != is_active:
                            membership.is_active = is_active
                            membership.save()

                            if not is_active:
                                # deactivated
                                MembershipPeriod.objects.filter(
                                    membership=membership,
                                    ended_at__isnull=True,
                                ).update(ended_at=datetime.date.today())
                            else:
                                # reactivated
                                MembershipPeriod.objects.create(membership=membership)

                else:
                    # role is NOT checked
                    if membership and membership.is_active:
                        # deactivate it
                        membership.is_active = False
                        membership.save()

                        MembershipPeriod.objects.filter(
                            membership=membership,
                            ended_at__isnull=True,
                        ).update(ended_at=datetime.date.today())

            selected_skills = {
                skill.id
                for skill in form.get_selected_skills()
            }

            existing_skills = {
                sp.skill.id: sp
                for sp in PersonSkill.objects.filter(person=self.person)
            }

            # adding skills
            for skill_id in selected_skills:
                if skill_id not in existing_skills:
                    PersonSkill.objects.create(
                        person=self.person,
                        skill_id=skill_id
                    )

            # deleting skills
            for skill_id, sp in existing_skills.items():
                if skill_id not in selected_skills:
                    sp.delete()

        return redirect("secondapp:org_member_list", username=self.kwargs["username"])


@method_decorator(login_required, name='dispatch')
class SongListView(ListView):
    model = Song
    template_name = "secondapp/song_dashboard.html"
    context_object_name = "songs"

    def get_queryset(self):
        username = self.kwargs["username"]
        return Song.objects.filter(
            user__username=username
        ).order_by("title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


@method_decorator(login_required, name='dispatch')
class SongDetailView(DetailView):
    model = Song
    template_name = "secondapp/song_page.html"
    context_object_name = "song"



@method_decorator(login_required, name='dispatch')
class SongCreateView(CreateView):
    form_class = SongForm
    template_name = "secondapp/song_form2.html"

    def form_valid(self, form):
        owner_username = self.kwargs["username"]
        # get auth user owner from username
        active_user = get_object_or_404(CustomUser, username=owner_username)
        form.instance.user = active_user # assign song to owner user (org or individual)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("secondapp:song_page",kwargs={
            "username": self.kwargs["username"],
            "pk": self.object.pk
        })


@method_decorator(login_required, name='dispatch')
class SongUpdateView(UpdateView):
    form_class = SongForm
    template_name = "secondapp/song_form2.html"


@method_decorator(login_required, name="dispatch")
class SongDeleteView(DeleteView):
    model = Song
    template_name = "secondapp/song_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("secondapp:song_dashboard", kwargs={"username":self.kwargs["username"]})


class SkillListAndCreateView(SkillListAndCreateMixin, View):
    pass


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
#             is_cancelled=False,
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
#             is_cancelled=False,
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