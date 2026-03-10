# mixins.py
from django.http import Http404
from django.views.generic import ListView, DeleteView, CreateView, UpdateView
from django.views.generic.edit import FormMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from .models import Organization, Role, Skill
from .forms import SkillForm
# from .models import Tag, Musician, Composer, Poet, Arranger, Member, Conductor
# from .forms import TagForm, ArrangerForm, MusicianForm, ComposerForm, PoetForm, ConductorForm, MemberForm
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.views.generic import DetailView
from .models import CustomUser
from .models import Event, EventPerson, EventSong



class SongOwnerMixin:
    """
    Handles owner fetching for all song views.
    For Detail/Update/Delete: also checks permission using permission_check_method.
    ListView/CreateView will just fetch owner_user; queryset/form handle filtering.
    """
    permission_check_method = None  # assign in view if needed

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        url_username = self.kwargs.get("username")
        self.owner_user = get_object_or_404(CustomUser, username=url_username)

    def dispatch(self, request, *args, **kwargs):
        # Only enforce permission for Detail/Update/Delete views
        if self.permission_check_method and hasattr(self, "get_object") and isinstance(self, DetailView):
            song = super().get_object(queryset=self.get_queryset())
            allowed = self.permission_check_method(request.user, song)
            if not allowed:
                raise PermissionDenied("You do not have permission")
        return super().dispatch(request, *args, **kwargs)


class SkillListAndCreateMixin(FormMixin, ListView):
    model = Skill
    form_class = SkillForm
    template_name = "secondapp/skill_list_create.html"
    context_object_name = "skills"

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        if "delete_skill" in request.POST:
            skill_id = request.POST.get("skill_id")
            print("Skill ID:", skill_id)
            skill = get_object_or_404(Skill, id=skill_id)
            skill.delete()
            return redirect(self.get_success_url())
        else:
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class AccountContextMixin:
    pass



#
# class RoleRequiredMixin:
#     """Role based rendering."""
#
#     allowed_roles = [Role.ADMIN]
#
#     def dispatch(self, request, *args, **kwargs):
#         username = self.kwargs.get("username")
#         if not username:
#             raise PermissionDenied("Organization not specified.")
#         try:
#             self.organization = Organization.objects.get(user__username=username)
#         except Organization.DoesNotExist:
#             raise PermissionDenied("Organization not found.")
#
#         # Get the user's Person
#         person = request.user.persons.first()
#
#         # Get the user's role in this organization
#         self.user_role = self.organization.get_role(request.user)
#
#         if not self.role_allowed(self.user_role):
#             raise PermissionDenied(f"Your role '{self.user_role}' does not have access.")
#
#         return super().dispatch(request, *args, **kwargs)
#
#     def role_allowed(self, user_role):
#         """Check if the user's role is allowed."""
#         if user_role is None:
#             return False
#         return user_role.pk in self.allowed_roles
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['user_role'] = self.user_role
#         context['organization'] = self.organization
#         return context

# class PersonRoleMixin:
#     role_model_from_map = {
#         "member": (Member, MemberForm),
#         "conductor": (Conductor, ConductorForm),
#         "musician": (Musician, MusicianForm),
#         "composer": (Composer, ComposerForm),
#         "poet": (Poet, PoetForm),
#         "arranger": (Arranger, ArrangerForm),
#     }
#
#     def get_model(self):
#         role = self.kwargs.get("role")
#         if role not in self.role_model_from_map:
#             raise Http404(f"invalid role {role} mixin error")
#         return self.role_model_from_map[role][0]
#
#     def get_form_class(self):
#         role = self.kwargs.get("role")
#         return self.role_model_from_map[role][1]
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["role"] = self.kwargs.get("role")
#         return context
#
#
# class BreadcrumbMixin:
#     def get_breadcrumbs(self):
#         parts = ['<a href="/">Home</a>']
#
#         if hasattr(self, 'section_name'):
#             section = self.section_name
#             parts.append(f'<a href="/{section}/">{section}</a>')
#
#             if hasattr(self, 'page_name'):
#                 page = self.page_name
#                 parts.append(page)
#
#         return ' > '.join(parts)
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['breadcrumbs'] = self.get_breadcrumbs()
#         return context