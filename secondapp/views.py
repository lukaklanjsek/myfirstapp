from django.shortcuts import render, get_object_or_404
#from django.http import Http404
# Create your views here.
from django.http import HttpResponse
from .models import Rehearsal


def index(request):
    latest_rehearsal_list = Rehearsal.objects.order_by("-pub_date")[:15]
    context = {"latest_rehearsal_list": latest_rehearsal_list}
    return render(request, "secondapp/index.html", context)


def detail(request, rehearsal_id):
    rehearsal = get_object_or_404(Rehearsal, pk=rehearsal_id)
    return render(request, "secondapp/detail.html", {"rehearsal": rehearsal})


#def results(request, memberrehearsal_id):
#    rehearsal = get_object_or_404(MemberRehearsal, pk=memberrehearsal_id)
#    return HttpResponse(request % rehearsal)

