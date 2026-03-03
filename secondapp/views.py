# views.py
import csv
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
from .models import Organization, Person, Membership, MembershipPeriod, Role, PersonSkill, PersonQuerySet, PersonRole

# from .forms import RehearsalForm, Member, ComposerForm, PoetForm, ArrangerForm, MusicianForm, SongForm, TagForm, PersonForm, EnsembleForm, ActivityForm, ImportFileForm
# from .models import Rehearsal, Member, Composer, Poet, Arranger, Musician, Song, Ensemble, Activity, Conductor, ImportFile
# from .mixins import TagListAndCreateMixin, PersonRoleMixin, BreadcrumbMixin, LoginRequiredMixin

from .models import CustomUser, Organization, Person, Membership, Role, Song, Skill
from .forms import RegisterForm, OrganizationForm, PersonForm, SongForm, SkillForm
from .forms import CustomUserCreationForm
from .mixins import  SkillListAndCreateMixin, SongOwnerMixin
from .permissions import AccessControl


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

    def get_object(self, queryset=None):

        # single user
        if not self.organization:
            return get_object_or_404(
                Person,
                user=self.request.user
            )

        # organization - ADMIN
        url_username = self.kwargs["username"]
        try:
            target_user = CustomUser.objects.get(username=url_username)
        except CustomUser.DoesNotExist:
            raise Http404("User not found")

        return get_object_or_404(
            AccessControl.get_viewable_people_queryset(self.request.user)
            .filter(memberships__user=target_user),
            id=self.kwargs["pk"]
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
                user=organization.user,    # this Person belongs to the organization
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
                membership=membership,
                person=person_admin,
                role_id=Role.ADMIN,
                started_at=datetime.date.today()
            )

        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class OrgMemberListView(ListView):
    """Shows all members of an organization."""
    template_name = "secondapp/org_member_list.html"
    context_object_name = "members"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        url_username = self.kwargs["username"]
        self.organization = get_object_or_404(
            Organization,
            user__username=url_username
        )

    def get_queryset(self):
        url_username = self.kwargs["username"]
        return AccessControl.get_visible_members(
            self.request.user,
            url_username
        ).select_related('person').prefetch_related('person__skills', "person__roles")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.organization

        # Add memberships to context for easier template access
        url_username = self.kwargs["username"]
        context["org_memberships"] = AccessControl.get_visible_members(
            self.request.user,
            url_username
        )

        return context

@method_decorator(login_required, name="dispatch")
class OrgMemberDetailView(DetailView):
    """Shows details of a Person owned by Organization."""
    model = Person
    template_name = "secondapp/org_member_detail.html"
    context_object_name = "person"

    def get_queryset(self):
        org_id = self.kwargs["org_id"]
        organization = get_object_or_404(Organization, id=org_id)
        url_username = self.kwargs["username"]
        # check user role
        viewer_role = AccessControl.get_org_roles(
            self.request.user,
            organization
        )
        if not viewer_role:
            raise PermissionDenied("No access to this organization")
        # get memberships
        visible_memberships = AccessControl.get_visible_members(
            self.request.user,
            url_username
        )
        # get only persons from this membership
        return Person.objects.filter(
            memberships__in=visible_memberships
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        url_username = self.kwargs["username"]

        context["person_data"] = AccessControl.filter_person_details(
            self.request.user,
            self.object,
            url_username,
        )

        return context


@method_decorator(login_required, name='dispatch')
class OrgMemberAddView( FormView):  # OrgMemberMixin,
    """Add new member."""
    template_name = "secondapp/org_member_form.html"
    form_class = OrgMemberForm

    def dispatch(self, request, *args, **kwargs):
        url_username = self.kwargs.get("username")

        if url_username:
            self.organization = get_object_or_404(
                Organization,
                user__username=url_username
            )
            if not AccessControl.has_permission(
                    request.user,
                    "update",
                    url_username
            ):
                return HttpResponseForbidden()
        else:
            self.organization = None

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        with transaction.atomic():
            # 1. create new person
            person = self._create_person(form)

            # 2. add roles into membership
            self._add_roles(person, form.cleaned_data["roles"])

            # 3. add skills
            self._add_skills(person, form.cleaned_data["skills"])

        return redirect(
            "secondapp:org_member_list",
            username=self.kwargs["username"]
        )

    def _create_person(self, form):
        """Create a new Person in an organization. (unclaimed by any real user)"""
        person = Person.objects.create(
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
            email=form.cleaned_data.get("email", ""),
            phone=form.cleaned_data.get("phone", ""),
            address=form.cleaned_data.get("address", ""),
            user=self.organization.user,  # linked to organization's auth acc
            owner=None  # profile not claimed by individual yet
        )
        return person

    def _add_roles(self, person, selected_roles):
        """Create memberships for selected roles."""
        today = datetime.date.today()

        # Create the base membership (only once per person-org relationship)
        membership, created = Membership.objects.get_or_create(
            user=self.organization.user,
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
                membership=membership,
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


@method_decorator(login_required, name='dispatch')
class OrgMemberEditView( FormView):  # OrgMemberMixin,
    """Edit existing member. Admin can edit everybody, user can edit its own."""
    template_name = "secondapp/org_member_form.html"
    form_class = OrgMemberForm


    def dispatch(self, request, *args, **kwargs):
        url_username = self.kwargs["username"]

        self.organization = get_object_or_404(
            Organization,
            user__username=url_username
        )

        self.person = get_object_or_404(Person, pk=self.kwargs["pk"])

        viewer_role = AccessControl.get_org_roles(
            request.user,
            url_username
        )

        is_admin = viewer_role.filter(id=Role.ADMIN).exists()
        is_owner = self.person.user == request.user

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
            current_skill_ids = self.person.person_skill.values_list(
                "skill_id", flat=True
            )

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
            }

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.organization
        return context

    def form_valid(self, form):
        with transaction.atomic():
            # 1. update person info
            self._update_person_info(form)

            # 2. update roles
            self._update_roles(form.cleaned_data["roles"])

            # 3. update skills
            self._update_skills(form.cleaned_data["skills"])

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
            user=self.organization.user,
            person=self.person
        )

        # Add new roles
        for role_id in (new_role_ids - current_role_ids):
            PersonRole.objects.create(
                person=self.person,
                role_id=role_id
            )
            MembershipPeriod.objects.create(
                membership=membership,
                person=self.person,
                role_id=role_id,
                started_at=today
            )

        # Remove roles
        removed_role_ids = current_role_ids - new_role_ids
        if removed_role_ids:
            # Close open periods for removed roles
            MembershipPeriod.objects.filter(
                membership=membership,
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


@method_decorator(login_required, name='dispatch')
class SongListView(SongOwnerMixin, ListView):
    model = Song
    template_name = "secondapp/song_dashboard.html"
    context_object_name = "songs"
    permission_check_method = AccessControl.can_view_song_list

    def get_queryset(self):
        # AccessControl handles personal vs org filtering
        return AccessControl.can_view_song_list(self.request.user, self.owner_user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["url_username"] = self.owner_user.username
        return context


@method_decorator(login_required, name='dispatch')
class SongDetailView(SongOwnerMixin, DetailView):
    model = Song
    template_name = "secondapp/song_page.html"
    context_object_name = "song"
    permission_check_method = AccessControl.can_view_song


@method_decorator(login_required, name='dispatch')
class SongCreateView(SongOwnerMixin, CreateView):
    form_class = SongForm
    template_name = "secondapp/song_form2.html"
    permission_check_method = AccessControl.can_manage_song

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.owner_user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.owner_user
        return super().form_valid(form)

    def get_success_url(self):
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

    def form_valid(self, form):
        form.instance.user = self.owner_user
        return super().form_valid(form)

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