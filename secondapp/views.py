from django.shortcuts import render, get_object_or_404
from django.http import Http404
# Create your views here.
from django.http import HttpResponse
from .models import RehearsalDate, AttendanceRecord


def index(request):
    latest_rehearsal_list = AttendanceRecord.objects.order_by("-pub_date")[:15]
    context = {"latest_rehearsal_list": latest_rehearsal_list}
    return render(request, "secondapp/index.html", context)


def detail(request, rehearsal_date):
    get_object_or_404(RehearsalDate, pk=rehearsaldate_id)
    return render(request, "secondapp/detail.html", {"rehearsal": rehearsal})


def results(request, attendance_id):
    attendance = get_object_or_404(AttendanceRecord, pk=attendance_id)
    return HttpResponse(response % attendance_id)


#def vote(request, rehearsal_date):
#    return HttpResponse("You're registring on attendance %s." % attendance_id)

def vote(request, rehearsal_date):
    attendance = get_object_or_404(AttendanceRecord, pk=date_record_id)
    try:
        selected_choice = attendee.attendance.get(pk=request.POST["attendance"])
    except (KeyError, Attendance.DoesNotExist):
        # Redisplay the question voting form.
        return render(
            request,
            "secondapp/detail.html",
            {
                    "attendance": attendance,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        selected_choice.votes = F("attendance") + 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("secondapp:results", args=(attendance.id,)))