from django.urls import path # , include


from . import views

app_name = 'secondapp'

urlpatterns = [

    path("signup/", views.SignUp.as_view(), name="signup"),

    path("<str:username>/person_form2/", views.PersonUpdateView.as_view(), name="person_update"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("login/", views.UserLoginView.as_view(), name="login"),

    path("home/", views.HomeView.as_view(), name="home"),

    path("", views.IndexView.as_view(), name="index2"),
    path("organization_form/", views.OrganizationCreateView.as_view(), name="org_create"),

    path("<str:username>/dashboard/", views.OrganizationDashboard.as_view(), name="org_dashboard"),
    path("<str:username>/<str:method>/import/", views.ImportDashboardView.as_view(), name="import_dashboard"),
    path("<str:username>/events/", views.EventListView.as_view(), name="event_list"),
    path("<str:username>/events/add/", views.EventCreateView.as_view(), name="event_create"),
    path("<str:username>/events/<int:pk>/", views.EventDetailView.as_view(), name="event_detail"),
    path("<str:username>/events/<int:pk>/edit/", views.EventUpdateView.as_view(), name="event_update"),
    # path('<str:username>/event/<int:pk>/toggle-lock/', views.ToggleEventLockView.as_view(), name='toggle_event_lock'),

    path("<str:username>/members/", views.OrgMemberListView.as_view(), name="org_member_list"),
    path("<str:username>/members/add/", views.OrgMemberAddView.as_view(),name="org_member_add"),
    path("<str:username>/members/add-composer/",
         views.OrgMemberAddView.as_view(),{'preset': 'composer'},name="org_member_add_composer"),
    path("<str:username>/members/add-poet/",
         views.OrgMemberAddView.as_view(),{'preset': 'poet'},name="org_member_add_poet"),
    path("<str:username>/members/add-translator/",
         views.OrgMemberAddView.as_view(),{'preset': 'translator'},name="org_member_add_translator"),
    path("<str:username>/members/<int:pk>/", views.OrgMemberDetailView.as_view(), name="org_member_detail"),
    path("<str:username>/members/<int:pk>/edit/", views.OrgMemberEditView.as_view(), name="org_member_edit"),

    path("<str:username>/songs/", views.SongListView.as_view(), name="song_dashboard"),
    path("<str:username>/songs/create/", views.SongCreateView.as_view(), name="song_form2"),
    path("<str:username>/songs/<int:pk>/", views.SongDetailView.as_view(), name="song_page"),
    path("<str:username>/songs/<int:pk>/update/", views.SongUpdateView.as_view(), name="song_form2"),
    path("<str:username>/songs/<int:pk>/delete/", views.SongDeleteView.as_view(), name="song_delete"),
    path('<str:username>/attendance/', views.AttendanceDashboardView.as_view(), name='attendance'),
    path('<str:username>/attendance/quick-add/', views.quick_add_rehearsal, name='quick_add_rehearsal'),
    path("skill/", views.SkillListAndCreateView.as_view(), name="skill"),


    #    path("", include("django.contrib.auth.urls")),

    # path("login/", views.AccountLoginView.as_view(), name="login"),
    #
    #
    # path("rehearsal/", views.RehearsalListView.as_view(), name="rehearsal_list"),
    # path("rehearsal/<int:pk>/", views.RehearsalDetailView.as_view(), name="rehearsal_detail"),
    # path("rehearsal/create/", views.RehearsalCreateView.as_view(), name="rehearsal_form"),
    # path("rehearsal/<int:pk>/update/", views.RehearsalUpdateView.as_view(), name="rehearsal_update"),
    # path("rehearsal/<int:pk>/confirm/", views.RehearsalDeleteView.as_view(), name="rehearsal_delete"),
    #
    # path("song/", views.SongListView.as_view(), name="song_list"),
    # path("song/<int:pk>/", views.SongDetailView.as_view(), name="song_detail"),
    # path("song/create/", views.SongCreateView.as_view(), name="song_form"),
    # path("song/<int:pk>/update/", views.SongUpdateView.as_view(), name="song_update"),
    # path("song/<int:pk>/delete/", views.SongDeleteView.as_view(), name="song_delete"),

    # path("tag/", views.TagListAndCreateView.as_view(), name="tag"),
    #
    # path("import/", views.ImportFileListView.as_view(), name="import_list"),
    # path("import/upload/", views.ImportFileFormView.as_view(), name="import_upload"),
    # path("import/<int:pk>/", views.ImportFileDetailView.as_view(), name="import_detail"),
    #
    # path("ensemble/", views.EnsembleListView.as_view(), name="ensemble_list"),
    # path("ensemble/<int:pk>/", views.EnsembleDetailView.as_view(), name="ensemble_detail"),
    # path("ensemble/create/", views.EnsembleCreateView.as_view(), name="ensemble_form"),
    # path("ensemble/<int:pk>/update/", views.EnsembleUpdateView.as_view(), name="ensemble_update"),
    # path("ensemble/<int:pk>/delete/", views.EnsembleDeleteView.as_view(), name="ensemble_delete"),
    #
    # path("<str:role>/", views.PersonListView.as_view(), name="person_list"),
    # path("<str:role>/<int:pk>/", views.PersonDetailView.as_view(), name="person_detail"),
    # path("<str:role>/create/", views.PersonCreateView.as_view(), name="person_form"),
    # path("<str:role>/<int:pk>/update/", views.PersonUpdateView.as_view(), name="person_update"),
    # path("<str:role>/<int:pk>/delete/", views.PersonDeleteView.as_view(), name="person_delete"),
    #
    # path("<str:role>/<int:pk>/activity/create/", views.ActivityCreateView.as_view(), name="activity_form"),
    # path("<str:role>/<int:pk>/activity/update/", views.ActivityUpdateView.as_view(), name="activity_update"),
    # path("<str:role>/<int:pk>/activity/delete/", views.ActivityDeleteView.as_view(), name="activity_confirm_delete"),

]