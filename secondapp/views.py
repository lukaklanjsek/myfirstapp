#from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
# Create your views here.
#from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.views import generic
from django.views.generic import ListView, CreateView, UpdateView
#from django.db.models import F

from .forms import RehearsalForm , SingerForm, ComposerForm, PoetForm, ArrangerForm, MusicianForm, SongForm
from .models import Rehearsal, Singer, Composer, Poet, Arranger, Musician, Song

# TODO complete making classes out of definitions and write appropriate html docs
#TODO STATIC FILES AND SHIT  --  i think statics are done for the basics already - unsure

class IndexView(generic.ListView):
    # TODO future rehearsals in a list of upcoming dates and locations  <---- this will be done some day
    template_name = "secondapp/index.html"

    def get_queryset(self):
        return Rehearsal.objects.order_by("-calendar")[:5]


class RehearsalListView(generic.ListView):
    template_name = "secondapp/rehearsal_list.html"
    context_object_name = "rehearsals"

    def get_queryset(self):
        return Rehearsal.objects.order_by("-calendar")


class RehearsalDetailView(generic.DetailView):
    model = Rehearsal
    template_name = "secondapp/rehearsal_detail.html"


class RehearsalCreateView(generic.CreateView):
    model = Rehearsal
    template_name = "secondapp/rehearsal_form.html"
    success_url = reverse_lazy("secondapp:rehearsal_detail")


class RehearsalUpdateView(generic.UpdateView):
    model = Rehearsal
    form_class = RehearsalForm
    template_name = "secondapp/rehearsal_form.html"
    success_url = "secondapp/rehearsal_detail.html"


class RehearsalDeleteView(generic.DeleteView):
    model = Rehearsal
    template_name = "secondapp/rehearsal_confirm_delete.html"
    success_url = "secondapp/rehearsal_list.html"


class SingerListView(generic.ListView):
    template_name = "secondapp/singer_list.html"
    context_object_name = "singers"

    def get_queryset(self):
        #trying to get all singers to show up first
        return Singer.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #seperating activity of singer
        active_singers = Singer.objects.filter(is_active=True)
        inactive_singers = Singer.objects.filter(is_active=False)
        context['active_singers'] = active_singers
        context['inactive_singers'] = inactive_singers

        return context


class SingerDetailView(generic.DetailView):
    model = Singer
    template_name = "secondapp/singer_detail.html"
    context_object_name = "singer"


class SingerCreateView(generic.CreateView):
    model = Singer
    form_class = SingerForm
    template_name = "secondapp/singer_form.html"
    success_url = reverse_lazy("secondapp:singer_detail")


class SingerUpdateView(generic.UpdateView):
    model = Singer
    form_class = SingerForm
    template_name = "secondapp/singer_form.html"
    success_url = "secondapp/singer_detail.html"


class SingerDeleteView(generic.DeleteView):
    model = Singer
    template_name = "secondapp/singer_confirm_delete.html"
    success_url = "secondapp/singer_list.html"


class SongListView(generic.ListView):
    model = Song
    template_name = "secondapp/song_list.html"
    context_object_name = "songs"

#    def get_queryset(self):
#        return Song.objects.all()


class SongDetailView(generic.DetailView):
    model = Song
    template_name = "secondapp/song_detail.html"
    context_object_name = "song"


class SongCreateView(generic.CreateView):
    model = Song
    form_class = SongForm
    template_name = "secondapp/song_form.html"
    success_url = reverse_lazy("secondapp:song_detail.html")


class SongUpdateView(generic.UpdateView):
    model = Song
    form_class = SongForm
    template_name = "secondapp/song_form.html"
    success_url = "secondapp/song_detail.html"


class SongDeleteView(generic.DeleteView):
    model = Song
    template_name = "secondapp/song_confirm_delete.html"
    success_url = "secondapp/song_list.html"


class PersonListView(ListView):
    template_name = "secondapp/"  # TODO HERE COMPLETE THIS SHIT


class PersonCreateView(CreateView):
    template_name = 'person_form.html'
    success_url = reverse_lazy('success_page')  # TODO Change this to your success URL

    def get_form_class(self):
        role = self.kwargs.get('role')
        if role == 'composer':
            return ComposerForm
        elif role == 'poet':
            return PoetForm
        elif role == 'arranger':
            return ArrangerForm
        elif role == 'musician':
            return MusicianForm
        else:
            return SingerForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role'] = self.kwargs.get('role')
        return context

class PersonUpdateView(UpdateView):
    template_name = 'person_form.html'
    success_url = reverse_lazy('success_page')  # TODO Change this to your success URL

    def get_form_class(self):
        if isinstance(self.object, Composer):
            return ComposerForm
        elif isinstance(self.object, Poet):
            return PoetForm
        elif isinstance(self.object, Arranger):
            return ArrangerForm
        elif isinstance(self.object, Musician):
            return MusicianForm
        else:
            return SingerForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role'] = self.object.__class__.__name__.lower()
        return context