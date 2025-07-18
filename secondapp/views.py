from django.shortcuts import render, get_object_or_404
# Create your views here.
from django.http import HttpResponse
from .models import Rehearsal, Singer


def index_rehearsal(request):
    latest_rehearsal_list = Rehearsal.objects.order_by("-calendar")[:15]
    context = {"latest_rehearsal_list": latest_rehearsal_list}
    return render(request, "secondapp/rehearsal_index.html", context)


def detail(request, rehearsal_id):
    rehearsal = get_object_or_404(Rehearsal, pk=rehearsal_id)
    return render(request, "secondapp/detail.html", {"rehearsal": rehearsal})


def index_singers(request):
    active_singers_list = Singer.objects.filter(is_active=True)
    context = {"active_singers_list": active_singers_list}
    return render(request, "secondapp/singer_index.html", context)