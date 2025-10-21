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

    path("import/", views.ImportFileListView.as_view(), name="import_list"),
    path("import/upload", views.ImportFileUpdateView.as_view(), name="import_upload"),
    path("import/detail", views.ImportFileDetailView.as_view(), name="import_detail"),

    path("ensemble/", views.EnsembleListView.as_view(), name="ensemble_list"),
    path("ensemble/<int:pk>/", views.EnsembleDetailView.as_view(), name="ensemble_detail"),
    path("ensemble/create/", views.EnsembleCreateView.as_view(), name="ensemble_form"),
    path("ensemble/<int:pk>/update/", views.EnsembleUpdateView.as_view(), name="ensemble_update"),
    path("ensemble/<int:pk>/delete/", views.EnsembleDeleteView.as_view(), name="ensemble_delete"),

    path("<str:role>/", views.PersonListView.as_view(), name="person_list"),
    path("<str:role>/<int:pk>/", views.PersonDetailView.as_view(), name="person_detail"),
    path("<str:role>/create/", views.PersonCreateView.as_view(), name="person_form"),
    path("<str:role>/<int:pk>/update/", views.PersonUpdateView.as_view(), name="person_update"),
    path("<str:role>/<int:pk>/delete/", views.PersonDeleteView.as_view(), name="person_delete"),

    path("<str:role>/<int:pk>/activity/create/", views.ActivityCreateView.as_view(), name="activity_form"),
    path("<str:role>/<int:pk>/activity/update/", views.ActivityUpdateView.as_view(), name="activity_update"),
    path("<str:role>/<int:pk>/activity/delete/", views.ActivityDeleteView.as_view(), name="activity_confirm_delete"),

]