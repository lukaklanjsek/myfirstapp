from django.urls import path

from . import views

app_name = 'secondapp'

urlpatterns = [

     path("", views.IndexView.as_view(), name="index"),

     path("rehearsal/", views.IndexRehearsalView.as_view(), name="rehearsal_index"),
     path("rehearsal/<int:pk>/", views.DetailRehearsalView.as_view(), name="rehearsal_detail"),
     path("rehearsal/<int:pk>/", views.ResultsRehearsalView.as_view(), name="rehearsal_results"),

     path("singer/", views.IndexSingerView.as_view(), name="singer_index"),
     path("singer/<int:pk>", views.DetailSingerView.as_view(), name="singer_detail"),

     path("song/", views.IndexSongView.as_view(), name="song_index"),
     path("song/<int:pk>", views.DetailSongView.as_view(), name="song_detail"),

]