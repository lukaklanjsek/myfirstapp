from django.urls import path

from . import views

app_name = 'secondapp'

urlpatterns = [

    path("", views.IndexView.as_view(), name="index"),

    path("rehearsal/", views.RehearsalListView.as_view(), name="rehearsal_list"),
    path("rehearsal/<int:pk>/", views.RehearsalDetailView.as_view(), name="rehearsal_detail"),
    path("rehearsal/create/", views.RehearsalCreateView.as_view(), name="rehearsal_form"),
    path("rehearsal/<int:pk>/update/", views.RehearsalUpdateView.as_view(), name="rehearsal_update"),
    path("rehearsal/<int:pk>/confirm/", views.RehearsalDeleteView.as_view(), name="rehearsal_delete"),

    path("song/", views.SongListView.as_view(), name="song_list"),
    path("song/<int:pk>/", views.SongDetailView.as_view(), name="song_detail"),
    path("song/create/", views.SongCreateView.as_view(), name="song_form"),
    path("song/<int:pk>/update/", views.SongUpdateView.as_view(), name="song_update"),
    path("song/<int:pk>/delete/", views.SongDeleteView.as_view(), name="song_delete"),

    path("tag/", views.TagListAndCreateView.as_view(), name="tag"),

    path("<str:role>/list/", views.PersonListView.as_view(), name="person_list"),
    path("<str:role>/<int:pk>/", views.PersonDetailView.as_view(), name="person_detail"),
    path("<str:role>/create/", views.PersonCreateView.as_view(), name="person_form"),
    path("<str:role>/<int:pk>/update/", views.PersonUpdateView.as_view(), name="person_update"),
    path("<str:role>/<int:pk>/delete/", views.PersonDeleteView.as_view(), name="person_delete"),

]