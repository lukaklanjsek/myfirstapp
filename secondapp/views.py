from django.shortcuts import render, get_object_or_404
# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic
from django.views.generic import ListView
from django.db.models import F

from .models import Rehearsal, Singer, Song

# TODO complete making classes out of definitions and write appropriate html docs


class IndexView(generic.ListView):
    # TODO future rehearsals in a list of upcoming dates and locations
    #latest_rehearsal_list = Rehearsal.objects.order_by("-calendar")[:15]
    #active_singers_list = Singer.objects.filter(is_active=True)
    #context = {latest_rehearsal_list: latest_rehearsal_list, active_singers_list: active_singers_list}
    #return render(request, "secondapp/homepage.html", context=context)
    #return HttpResponse("Hello, world. You're at the homepage home page.")
    template_name = "secondapp/index.html"
    context_object_name = "latest_rehearsal_list"

    def get_queryset(self):
        """Return the last ten rehearsals."""
        return Rehearsal.objects.order_by("-calendar")[:10]


class IndexRehearsalView(generic.ListView):
    template_name = "secondapp/rehearsal_index.html"
    context_object_name = "latest_rehearsal_list"

    def get_queryset(self):
        """Return the last 45 rehearsals."""
        return Rehearsal.objects.order_by("-calendar")[:45]


class DetailRehearsalView(generic.DetailView):
    model = Rehearsal
    template_name = "secondapp/rehearsal_detail.html"


class IndexSingerView(generic.ListView):
    template_name = "secondapp/singer_index.html"
    context_object_name = "active_singers_list"

    def get_queryset(self):
        """Return all active singers."""
        return Singer.objects.filter(is_active=True)


#def index_singers_inactive(request):
#    inactive_singers_list = Singer.objects.filter(is_active=False)
#    context = {"inactive_singers_list": inactive_singers_list}
#    return render(request, "secondapp/singer_index.html", context)


class DetailSingerView(generic.DetailView):
    model = Singer
    template_name = "secondapp/singer_detail.html"

#    return render(request, template_name="secondapp/singer_detail.html", context={"singer": singer})


#def index_songs(request):
#    return HttpResponse(request, "Hello, world. You're at the songs index.")

#def detail_song(request):
#    song = get_object_or_404(Song, pk=song_id)
#    return render(request, template_name="secondapp/song_detail.html", context={"song": song})