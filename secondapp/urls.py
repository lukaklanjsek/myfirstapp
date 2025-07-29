from django.urls import path

from . import views

app_name = 'secondapp'

urlpatterns = [

     path("", views.IndexView.as_view(), name="index"),


     path("rehearsal/", views.IndexRehearsalView.as_view(), name="rehearsal_index"),
     path("rehearsal/<int:pk>/", views.DetailRehearsalView.as_view(), name="rehearsal_detail"),

     path("singer/", views.IndexSingerView.as_view(), name="singer_index"),
     #path("singer_inactive", views.index_singers_inactive, name="index_singers_inactive"),
     path("singer/<int:pk>", views.DetailSingerView.as_view(), name="singer_detail"),

]