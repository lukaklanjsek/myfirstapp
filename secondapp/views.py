from django.http import HttpRequest, HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from datetime import datetime, timedelta
from django.utils import timezone
#from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.views import generic
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View, FormView
from django.views.generic.edit import DeleteView
from django.db.models import Q
from django.apps import apps
from django.conf import settings
import os
import csv



from .forms import RehearsalForm, SingerForm, ComposerForm, PoetForm, ArrangerForm, MusicianForm, SongForm, TagForm, PersonForm, EnsembleForm, ActivityForm, ImportFileForm
from .models import Rehearsal, Singer, Composer, Poet, Arranger, Musician, Song, Ensemble, Activity, Conductor, ImportFile
from .mixins import TagListAndCreateMixin, PersonRoleMixin

class IndexView(generic.ListView):
    model = Rehearsal
    template_name = "secondapp/index.html"
    context_object_name = "rehearsal_list"
    queryset = Rehearsal.objects.filter(is_cancelled=False).order_by('-calendar')[:20]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        paginated_rehearsals = context["rehearsal_list"]

        context["upcoming_rehearsals"] = [
            rehearsal for rehearsal in paginated_rehearsals
            if rehearsal.calendar > now
        ]
        context["past_rehearsals"] = [
            rehearsal for rehearsal in paginated_rehearsals
            if rehearsal.calendar < now
        ]

        for rehearsal in context['upcoming_rehearsals']:
            rehearsal.singer_status = rehearsal.get_singer_status()

        for rehearsal in context['past_rehearsals']:
            rehearsal.singer_status = rehearsal.get_singer_status()

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
    paginate_by = 20

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

        for rehearsal in context['upcoming_rehearsals']:
            rehearsal.singer_status = rehearsal.get_singer_status()

        for rehearsal in context['past_rehearsals']:
            rehearsal.singer_status = rehearsal.get_singer_status()

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rehearsal = self.object
        now = timezone.now()
        singer_status = rehearsal.get_singer_status()
        context.update(singer_status)

        return context


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

    def get_base_queryset(self):
        model = self.get_model()
        queryset = model.objects.all().order_by("last_name")

        search_query = self.request.GET.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        return queryset

    def get_queryset(self):
        queryset = self.get_base_queryset
        model = self.get_model()

        if hasattr(model, "is_active"):
            return queryset

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_queryset = self.get_base_queryset()
        model = self.get_model()

        if hasattr(model, 'is_active'):
            context["active_people"] = base_queryset.filter(is_active=True)
            context["inactive_people"] = base_queryset.filter(is_active=False)
            context["has_voice"] = True

            all_rehearsals = Rehearsal.objects.filter(is_cancelled=False).count()
            for person in context["active_people"]:
                attendance = person.get_rehearsal_attendance()
                person.missing_count = attendance["missing"].count()
                person.total_rehearsals = all_rehearsals

            for person in context["inactive_people"]:
                attendance = person.get_rehearsal_attendance()
                person.missing_count = attendance["missing"].count()
                person.total_rehearsals = all_rehearsals

        else:
            context["active_people"] = base_queryset
            context["inactive_people"] = base_queryset.none()
            context["has_voice"] = False

        context["search_query"] = self.request.GET.get("search", "")

        return context


class PersonDetailView(PersonRoleMixin, DetailView):
    template_name = 'secondapp/person_detail.html'
    context_object_name = 'person'

    def get_object(self, queryset=None):
        return self.get_model().objects.get(pk=self.kwargs.get('pk'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = self.object

        if isinstance(person, Singer):
            attendance = person.get_rehearsal_attendance()
            context.update(attendance)

        context["activity"] = person.activity.all()

        return context


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


# ---------------------------------------------

class EnsembleListView(generic.ListView):
    model = Ensemble
    template_name = "secondapp/ensemble_list.html"
    context_object_name = "ensemble_list"


class EnsembleDetailView(generic.DetailView):
    model = Ensemble
    template_name = "secondapp/ensemble_detail.html"
    context_object_name = "ensemble"


class EnsembleCreateView(generic.CreateView):
    model = Ensemble
    form_class = EnsembleForm
    template_name = "secondapp/ensemble_form.html"

    def get_success_url(self):
        return reverse_lazy("secondapp:ensemble_detail", kwargs={"pk": self.object.pk})


class EnsembleUpdateView(generic.UpdateView):
    model = Ensemble
    form_class = EnsembleForm
    template_name = "secondapp/ensemble_form.html"

    def get_success_url(self):
        return reverse_lazy("secondapp:ensemble_detail", kwargs={"pk": self.object.pk})


class EnsembleDeleteView(generic.DeleteView):
    model = Ensemble
    template_name = "secondapp/ensemble_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("secondapp:ensemble_list")

# ---------------------------------------------

class ActivityCreateView(generic.CreateView):
    model = Activity
    fields = ["start_date", "end_date", "ensemble"]
    template_name = "secondapp/activity_form.html"

    def form_valid(self, form):
        role = self.kwargs["role"]
        person_id = self.kwargs["pk"]

        if role == "singer":
            form.instance.singer = Singer.objects.get(pk=person_id)
        elif role == "conductor":
            form.instance.conductor = Conductor.objects.get(pk=person_id)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["role"] = self.kwargs["role"]
        person_id = self.kwargs["pk"]
        if context["role"] == "singer":
            context["person"] = Singer.objects.get(pk=person_id)
        elif context["role"] == "conductor":
            context["person"] = Conductor.objects.get(pk=person_id)
        return context

    def get_success_url(self):
        return self.object.get_absolute_url()

class ActivityUpdateView(generic.UpdateView):
    model = Activity
    fields = ["start_date", "end_date", "ensemble"]
    template_name = "secondapp/activity_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.singer:
            context["person"] = self.object.singer
            context["role"] = "singer"
        elif self.object.conductor:
            context["person"] = self.object.conductor
            context["role"] = "conductor"
        return context

    def get_success_url(self):
        return self.object.get_absolute_url()


class ActivityDeleteView(generic.DeleteView):
    model = Activity
    template_name = "secondapp/activity_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.singer:
            context["person"] = self.object.singer
            context["role"] = "singer"
        elif self.object.conductor:
            context["person"] = self.object.conductor
            context["role"] = "conductor"
        return context

    def get_success_url(self):
        if self.object.singer:
            return self.object.singer.get_absolute_url()
        elif self.object.conductor:
            return self.object.conductor.get_absolute_url()
        return "/"

#---------------------------------------------------------

class ImportFileListView(generic.ListView):
    model = ImportFile
    template_name = "secondapp/import_list.html"
    context_object_name = "import_list"


#def handle_uploaded_file(f):
#    upload_path = os.path.join(settings.MEDIA_ROOT, f.name)
#    with open(upload_path, 'wb+') as destination:
#        for chunk in f.chunks():
#            destination.write(chunk)


class ImportFileUpdateView(generic.UpdateView):
    form_class = ImportFileForm
    template_name = "secondapp/import_upload.html"
    success_url = reverse_lazy("secondapp:import_list")


class ImportFileDetailView(generic.DetailView):
    model = ImportFile
    template_name = "secondapp/import_detail.html"
    context_object_name = "import_detail"

