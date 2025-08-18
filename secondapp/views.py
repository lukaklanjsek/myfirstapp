#from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from datetime import datetime, timedelta
from django.utils import timezone
#from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.views import generic
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.db.models import Q

from .forms import RehearsalForm, SingerForm, ComposerForm, PoetForm, ArrangerForm, MusicianForm, SongForm, TagForm, \
    PersonForm
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


# -----------------------------------------
class SingerListView(generic.ListView):
    model = Singer
    template_name = "secondapp/singer_list.html"
    context_object_name = "singers"

    def get_queryset(self):
        queryset = Singer.objects.all().order_by("voice", "last_name")

        search_query = self.request.GET.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(voice__icontains=search_query)
            )

        return queryset


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_singers = self.get_queryset()
        context["active_singers"] = all_singers.filter(is_active=True)
        context["inactive_singers"] = all_singers.filter(is_active=False)
        context["search_query"] = self.request.GET.get("search", "")

        return context


class SingerDetailView(generic.DetailView):
    model = Singer
    template_name = "secondapp/singer_detail.html"
    context_object_name = "singer"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recent_rehearsals"] = self.object.rehearsal_set.all()[:5]
        return context


class SingerCreateView(generic.CreateView):
    model = Singer
    form_class = SingerForm
    template_name = "secondapp/singer_form.html"

    def get_success_url(self):
        return reverse_lazy("secondapp:singer_detail", kwargs={"pk": self.object.pk})



class SingerUpdateView(generic.UpdateView):
    model = Singer
    form_class = SingerForm
    template_name = "secondapp/singer_form.html"

    def get_success_url(self):
        return reverse_lazy("secondapp:singer_detail", kwargs={"pk": self.object.pk})



class SingerDeleteView(generic.DeleteView):
    model = Singer
    template_name = "secondapp/singer_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("secondapp:singer_list")


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

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_people = self.get_queryset()

#        if hasattr(all_people.model, 'is_active'):
#            context["active_people"] = all_people.filter(is_active=True)
#            context["inactive_people"] = all_people.filter(is_active=False)

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
    template_name = 'secondapp/person_confirm_delete.html'
    success_url = reverse_lazy('success_page')

    def get_object(self, queryset=None):
        return self.get_model().objects.get(pk=self.kwargs.get('pk'))

    def get_success_url(self):
        return reverse_lazy(
            "secondapp:person_list",
            kwargs={
                "role": self.kwargs.get('role')
            }
        )