from django.urls import path

from . import views

app_name = 'secondapp'

urlpatterns = [

     path("", views.IndexView.as_view(), name="index"),

     path("rehearsal/", views.RehearsalListView.as_view(), name="rehearsal_list"),
     path("rehearsal/<int:pk>/", views.RehearsalDetailView.as_view(), name="rehearsal_detail"),
     path("rehearsal/create/", views.RehearsalCreateView.as_view(), name="rehearsal_form"),
     path("rehearsal/<int:pk>/update/", views.RehearsalUpdateView.as_view(), name="rehearsal_update"),
     path("rehearsal/confirm/<int:pk>/", views.RehearsalDeleteView.as_view(), name="rehearsal_delete"),

     path("singer/", views.SingerListView.as_view(), name="singer_list"),
     path("singer/<int:pk>/", views.SingerDetailView.as_view(), name="singer_detail"),
     path("singer/create/", views.SingerCreateView.as_view(), name="singer_form"),
     path("singer/<int:pk>/update/", views.SingerUpdateView.as_view(), name="singer_update"),
     path("singer/<int:pk>/delete/", views.SingerDeleteView.as_view(), name="singer_delete"),

     path("song/", views.SongListView.as_view(), name="song_list"),
     path("song/<int:pk>/", views.SongDetailView.as_view(), name="song_detail"),
     path("song/create/", views.SongCreateView.as_view(), name="song_form"),
     path("song/<int:pk>/update/", views.SongUpdateView.as_view(), name="song_update"),
     path("song/<int:pk>/delete/", views.SongDeleteView.as_view(), name="song_delete"),

]