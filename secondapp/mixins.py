# mixins.py
from django.http import Http404
from django.views.generic import ListView, DeleteView, CreateView, UpdateView
from django.views.generic.edit import FormMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from .models import Tag, Musician, Composer, Poet, Arranger, Member, Conductor
from .forms import TagForm, ArrangerForm, MusicianForm, ComposerForm, PoetForm, ConductorForm, MemberForm


class TagListAndCreateMixin(FormMixin, ListView):
    model = Tag
    form_class = TagForm
    template_name = "secondapp/tag_list_create.html"
    context_object_name = "tags"

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        if "delete_tag" in request.POST:
            tag_id = request.POST.get("tag_id")
            print("Tag ID:", tag_id)
            tag = get_object_or_404(Tag, id=tag_id)
            tag.delete()
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


class PersonRoleMixin:
    role_model_from_map = {
        "member": (Member, MemberForm),
        "conductor": (Conductor, ConductorForm),
        "musician": (Musician, MusicianForm),
        "composer": (Composer, ComposerForm),
        "poet": (Poet, PoetForm),
        "arranger": (Arranger, ArrangerForm),
    }

    def get_model(self):
        role = self.kwargs.get("role")
        if role not in self.role_model_from_map:
            raise Http404(f"invalid role {role} mixin error")
        return self.role_model_from_map[role][0]

    def get_form_class(self):
        role = self.kwargs.get("role")
        return self.role_model_from_map[role][1]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["role"] = self.kwargs.get("role")
        return context
    
    
class BreadcrumbMixin:
    def get_breadcrumbs(self):
        parts = ['<a href="/">Home</a>']

        if hasattr(self, 'section_name'):
            section = self.section_name
            parts.append(f'<a href="/{section}/">{section}</a>')

            if hasattr(self, 'page_name'):
                page = self.page_name
                parts.append(page)
                
        return ' > '.join(parts)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        return context