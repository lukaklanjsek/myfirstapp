import csv
from dataclasses import field
from fileinput import filename
import sqlite3

from django.core.files.uploadedfile import UploadedFile
from django.db import connection
from django.http import HttpRequest, HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template.context_processors import request
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


from .forms import RehearsalForm, Member, ComposerForm, PoetForm, ArrangerForm, MusicianForm, SongForm, TagForm, PersonForm, EnsembleForm, ActivityForm, ImportFileForm
from .models import Rehearsal, Member, Composer, Poet, Arranger, Musician, Song, Ensemble, Activity, Conductor, ImportFile
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
            rehearsal.member_status = rehearsal.get_member_status()

        for rehearsal in context['past_rehearsals']:
            rehearsal.member_status = rehearsal.get_member_status()

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
            rehearsal.member_status = rehearsal.get_member_status()

        for rehearsal in context['past_rehearsals']:
            rehearsal.member_status = rehearsal.get_member_status()

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
        member_status = rehearsal.get_member_status()
        context.update(member_status)

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

        if isinstance(person, Member):
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

        if role == "member":
            form.instance.member = Member.objects.get(pk=person_id)
        elif role == "conductor":
            form.instance.conductor = Conductor.objects.get(pk=person_id)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["role"] = self.kwargs["role"]
        person_id = self.kwargs["pk"]
        if context["role"] == "member":
            context["person"] = Member.objects.get(pk=person_id)
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
        if self.object.member:
            context["person"] = self.object.member
            context["role"] = "member"
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
        if self.object.member:
            context["person"] = self.object.member
            context["role"] = "member"
        elif self.object.conductor:
            context["person"] = self.object.conductor
            context["role"] = "conductor"
        return context

    def get_success_url(self):
        if self.object.member:
            return self.object.member.get_absolute_url()
        elif self.object.conductor:
            return self.object.conductor.get_absolute_url()
        return "/"

#---------------------------------------------------------

class ImportFileListView(generic.ListView):
    model = ImportFile
    template_name = "secondapp/import_list.html"
    context_object_name = "import_list"



class ImportFileFormView(generic.FormView):
    form_class = ImportFileForm
    model = ImportFile
    template_name = "secondapp/import_upload.html"
    success_url = reverse_lazy("secondapp:import_detail")

    def form_valid(self, form):
        import_mode = form.cleaned_data["import_mode"]
        uploaded_file = self.request.FILES["file"]

        # TEST # -----  detected encoding: Windows-1250 ##################

        if import_mode == "members":
            default_db_loc = settings.DATABASES['default']['NAME']
            conn = sqlite3.connect(default_db_loc)
            crsr = connection.cursor()

            print("connected to the database")

            lines = uploaded_file.read().decode("cp1250").splitlines()    # "cp1250"  "utf-8"    <------------ SET "decode"
            reader = csv.DictReader(lines, delimiter=';')

#            print("print post dictreader:", reader)    #  ->  TEST PRINT

            new_keys = ("first_name", "last_name", "third_name")
#            parts = {}

            for row in reader:

                # 1. check if ensemble exists  /  if not, create one (hardcoded)
                # 2. check if conductor exists  /  if not, create one (hardcoded)
                # 3. check if member exists  / if not, create one
                # 4. check if activity exists  /  if not, add it (add multiple) !!! connect member conductor ensemble !!!

#                print("TEST PRINT ROWS:", row)  #  ->     TEST PRINT
                # 1. check if ensemble exists
                crsr.execute("SELECT 1 FROM secondapp_ensemble WHERE name LIKE 'De Profundis'")
                ensemble = crsr.fetchone()
                print("return of fetchall", ensemble)
                if ensemble is 1: continue
                else: crsr.execute("INSERT INTO secondapp_ensemble(name, address, created_at, updated_at) VALUES('De Profundis', 'Kovačičeva 2', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP")
                conn.commit()

                # 2. check if conductor exists
                crsr.execute("SELECT 1 FROM secondapp_conductor WHERE first_name LIKE 'Branka' AND last_name LIKE 'Potočnik' AND third_name LIKE 'Krajnik'")
                conductor = crsr.fetchone()
                if conductor is 1: continue
                else: crsr.execute("INSERT INTO secondapp_conductor")
                #   DOKONČAJ ----------------------------------------------------------------------------------------------

                if "Ime in priimek" in row:

                    parts = row["Ime in priimek"].split(" ")

#                    print("print post split row:", parts)    #  ->  TEST PRINT

                    name_together = dict(zip(new_keys, parts))

                    print("after zip:", name_together)     #  ->  TEST PRINT

                else:
                    print("no 'Ime in priimek' in row")   #  ->   TEST PRINT

                addr_together = {"address":row["Naslov"], "email":row["e-pošta"], "phone_number":row["Telefon"], "mobile_number":row["Mobilc"]}

                print("ADDRESS:", addr_together)    #  ->   TEST PRINT

                bday = {"birth_date":row["Datum roj."]}

                print("BDAY:", bday)    #   ->    TEST PRINT

#                print("voice pre-IF:", row["Glas"])

                if "Glas" in row:
                    glas = row["Glas"]

                    if glas == "Alt":
                        voice_dict = {"voice":"Alto"}
                    elif glas == "Sopran":
                        voice_dict = {"voice":"Soprano"}
                    elif glas == "Tenor":
                        voice_dict = {"voice":"Tenor"}
                    elif glas == "Bas":
                        voice_dict = {"voice":"Bass"}
                    else:
                        voice_dict = {}
                else:
                    pass    #   --------------------

                print("Voice post-IF:", voice_dict)

                if "Aktiven" in row:
                    date_range = row["Aktiven"].split(",")
#                    print("first date split:", date_range)    #  ->   TEST PRINT
                    trajanje = []
                    for obdobje in date_range:
                        seznam = obdobje.split("-")
                        if len(seznam) >= 3:
                            beginning = "-".join(seznam[0:3])
                        else:
                            beginning = None
                        if len(seznam) >= 6:
                            finish = "-".join(seznam[3:6])
                        else:
                            finish = None
                        trajanje.append((beginning, finish))

#                        print("trajanje pre-FOR:", trajanje)    #  ->   TEST PRINT
#                    print("trajanje after FOR:", trajanje)    #  ->    TEST PRINT
                    currently = False
                    for (a,b) in trajanje:
                        if a is not None and b is not None:
                            continue
                        elif a is None and b is None:
                            continue
                        else:
                            currently = True
#                    print("TEST currently:", currently)    #  ->    TEST PRINT
                    if currently is True:
                        right_now = {"is_active": True}
                    else:
                        right_now = {"is_active": False}
                    print("TEST activity:", right_now)     #  ->    TEST PRINT

#                print("trajanje level-ROW:", trajanje)

    #      ------------------------------------------------------
#            print("outside if loop:", new_keys)
#            print("outside if loop:", parts)

            conn.close()
            print("connection closed")



            self.object = form.save()
            uploaded_file.close()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("secondapp:import_detail", kwargs={"pk": self.object.pk})


class ImportFileDetailView(generic.DetailView):
    model = ImportFile
    template_name = "secondapp/import_detail.html"
    context_object_name = "import_detail"