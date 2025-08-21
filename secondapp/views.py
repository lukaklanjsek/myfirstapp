from django.http import HttpRequest, HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from datetime import datetime, timedelta
from django.utils import timezone
#from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.views import generic
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.views.generic.edit import DeleteView
from django.db.models import Q

from .forms import RehearsalForm, SingerForm, ComposerForm, PoetForm, ArrangerForm, MusicianForm, SongForm, TagForm, PersonForm
from .models import Rehearsal, Singer, Composer, Poet, Arranger, Musician, Song
from .mixins import TagListAndCreateMixin, PersonRoleMixin

# TODO complete making classes out of definitions and write appropriate html docs
#TODO STATIC FILES AND SHIT  --  i think statics are done for the basics already - unsure

class IndexView(generic.ListView):
    model = Rehearsal
    template_name = "secondapp/index.html"
    context_object_name = "rehearsal_list"
    queryset = Rehearsal.objects.all().order_by('-calendar')[:5]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()


        happening_now = Rehearsal.objects.filter(
            is_cancelled=False,
            calendar__gte=now - timedelta(minutes=660),
            calendar__lte=now + timedelta(minutes=660)
        ).first()

        context['happening_now'] = happening_now
        return context


# ---------------------------------------
class RehearsalListView(generic.ListView):
    template_name = "secondapp/rehearsal_list.html"
    context_object_name = "rehearsal_list"
    paginate_by = 7

    def get_queryset(self):
        return Rehearsal.objects.filter(is_cancelled=False).order_by("-calendar")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        paginated_rehearsals = context['rehearsal_list']
        context['upcoming_rehearsals'] = [
            rehearsal for rehearsal in paginated_rehearsals
            if rehearsal.calendar >= now
        ]
        context['past_rehearsals'] = [
            rehearsal for rehearsal in paginated_rehearsals
            if rehearsal.calendar < now
        ]

        happening_now = Rehearsal.objects.filter(
            is_cancelled=False,
            calendar__gte=now - timedelta(minutes=660),
            calendar__lte=now + timedelta(minutes=660)
        ).first()

        context['happening_now'] = happening_now
        return context


class RehearsalDetailView(generic.DetailView):
    model = Rehearsal
    template_name = "secondapp/rehearsal_detail.html"


class RehearsalCreateView(generic.CreateView):
    model = Rehearsal
    form_class = RehearsalForm
    template_name = "secondapp/rehearsal_form.html"

    def get_success_url(self):
        return reverse_lazy("secondapp:rehearsal_detail", kwargs={"pk": self.object.pk})


class RehearsalUpdateView(generic.UpdateView):
    model = Rehearsal
    form_class = RehearsalForm
    template_name = "secondapp/rehearsal_form.html"

    def get_success_url(self):
        return reverse_lazy("secondapp:rehearsal_detail", kwargs={"pk": self.object.pk})


class RehearsalDeleteView(generic.DeleteView):
    model = Rehearsal
    template_name = "secondapp/rehearsal_confirm.html"

    def get_success_url(self):
        return reverse_lazy("secondapp:rehearsal_list")



# -------------------------------------------
class SongListView(generic.ListView):
    model = Song
    template_name = "secondapp/song_list.html"
    context_object_name = "song_list"

    def get_queryset(self):
        queryset = Song.objects.all()

        search_query = self.request.GET.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(genre__icontains=search_query) |
                Q(composer__last_name__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        return context


class SongDetailView(generic.DetailView):
    model = Song
    template_name = "secondapp/song_detail.html"
    context_object_name = "song"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recent_rehearsals"] = self.object.rehearsal_set.all()[:5:]
        return context


class SongCreateView(generic.CreateView):
    model = Song
    form_class = SongForm
    template_name = "secondapp/song_form.html"

    def get_success_url(self):
        return reverse_lazy("secondapp:song_detail", kwargs={"pk": self.object.pk})


class SongUpdateView(generic.UpdateView):
    model = Song
    form_class = SongForm
    template_name = "secondapp/song_form.html"

    def get_success_url(self):
        return reverse_lazy("secondapp:song_detail", kwargs={"pk": self.object.pk})


class SongDeleteView(generic.DeleteView):
    model = Song
    template_name = "secondapp/song_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("secondapp:song_list")


# ----------------------------------------
class TagListAndCreateView(TagListAndCreateMixin, View):
    pass


# ---------------------------------------------------------
class PersonListView(PersonRoleMixin, ListView):
    template_name = "secondapp/person_list.html"
    context_object_name = "people"

    def get_queryset(self):
        model = self.get_model()
        queryset = model.objects.all().order_by("last_name")

        search_query = self.request.GET.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )

        if hasattr(model, "is_active"):
            queryset = queryset.filter(is_active=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_people = self.get_queryset()
        model = self.get_model()

        if hasattr(model, 'is_active'):
            context["active_people"] = all_people.filter(is_active=True)
            context["inactive_people"] = all_people.filter(is_active=False)

        context["search_query"] = self.request.GET.get("search", "")

        return context


class PersonDetailView(PersonRoleMixin, DetailView):
    template_name = 'secondapp/person_detail.html'
    context_object_name = 'person'

    def get_object(self, queryset=None):
        return self.get_model().objects.get(pk=self.kwargs.get('pk'))


class PersonCreateView(PersonRoleMixin, CreateView):
    template_name = "secondapp/person_form.html"

    def get_success_url(self):
        return reverse_lazy("secondapp:person_detail", kwargs={"role": self.kwargs.get('role'), "pk": self.object.pk})


class PersonUpdateView(PersonRoleMixin, UpdateView):
    template_name = "secondapp/person_form.html"
    context_object_name = "person"

    def get_object(self, queryset = None):
        return self.get_model().objects.get(pk=self.kwargs.get("pk"))

    def get_success_url(self):
        return reverse_lazy(
            "secondapp:person_detail",
            kwargs={
                "role": self.kwargs.get('role'),
                "pk": self.object.pk
            }
        )


class PersonDeleteView(PersonRoleMixin, DeleteView):
    model = "person"
    template_name = 'secondapp/person_confirm_delete.html'
    context_object_name = "person"

    def dispatch(self, request, *args, **kwargs):
        self.model = self.get_model()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["role"] = self.kwargs.get("role")
        return context

    def get_object(self, queryset = None):
        model = self.get_model()
        pk = self.kwargs.get("pk")
        try:
            return model.objects.get(pk=pk)
        except model.DoesNotExist:
            raise Http404(f"{model.__name__} with id {pk} does not exist")

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        self.object.delete()

        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        role = self.kwargs.get("role")
        return reverse_lazy("secondapp:person_list", kwargs={"role": role})