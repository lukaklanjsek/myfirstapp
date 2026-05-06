from django.urls import path # , include


from . import views

app_name = 'syncope'

urlpatterns = [

    path("signup/", views.SignUp.as_view(), name="signup"),

    path("<str:username>/person_form2/", views.PersonUpdateView.as_view(), name="person_update"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("login/", views.UserLoginView.as_view(), name="login"),

    path("home/", views.HomeView.as_view(), name="home"),

    path("", views.IndexView.as_view(), name="index2"),
    path("organization_form/", views.OrganizationCreateView.as_view(), name="org_create"),

    path("<str:username>/dashboard/", views.OrganizationDashboard.as_view(), name="org_dashboard"),
    path("<str:username>/import/", views.ImportHubView.as_view(), name="import_hub"),
    path("<str:username>/import/combine/", views.CombineProjectsView.as_view(), name="import_combine"),
    path("<str:username>/<str:method>/import/", views.ImportDashboardView.as_view(), name="import_dashboard"),
    path("<str:username>/events/", views.EventListView.as_view(), name="event_list"),
    path("<str:username>/events/add/", views.EventCreateView.as_view(), name="event_create"),
    path("<str:username>/events/<int:pk>/", views.EventDetailView.as_view(), name="event_detail"),
    path("<str:username>/events/<int:pk>/edit/", views.EventUpdateView.as_view(), name="event_update"),
    path("<str:username>/events/<int:event_pk>/attendance/update/", views.self_attendance_update, name="self_attendance_update"),
    path("<str:username>/events/<int:pk>/attendance/add/", views.event_add_attendance, name="event_add_attendance"),
    path("<str:username>/events/<int:event_pk>/attendance/<int:pk>/delete/", views.AttendanceDeleteView.as_view(), name="attendance_delete"),
    path("<str:username>/events/<int:pk>/songs/add/", views.event_add_song, name="event_add_song"),

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
    path("<str:username>/songs/<int:pk>/update/", views.SongUpdateView.as_view(), name="song_update"),
    path("<str:username>/songs/<int:pk>/delete/", views.SongDeleteView.as_view(), name="song_delete"),
    path("<str:username>/songs/<int:pk>/quotes/", views.SongQuoteView.as_view(), name="song_quotes"),
    path('<str:username>/attendance/', views.AttendanceDashboardView.as_view(), name='attendance'),
    path('<str:username>/attendance/quick-add/', views.quick_add_rehearsal, name='quick_add_rehearsal'),
    path("skill/", views.SkillListAndCreateView.as_view(), name="skill"),

    path('<str:username>/projects/', views.ProjectListView.as_view(), name='project_list'),
    path('<str:username>/projects/new/', views.ProjectCreateView.as_view(), name='project_create'),
    path('<str:username>/projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('<str:username>/projects/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_update'),
    path('<str:username>/projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
    path('<str:username>/projects/<int:pk>/events/add/', views.project_add_event, name='project_add_event'),
    path('<str:username>/projects/<int:pk>/events/<int:event_pk>/remove/', views.project_remove_event, name='project_remove_event'),
    path('<str:username>/projects/<int:pk>/songs/add/', views.project_add_song, name='project_add_song'),
    path('<str:username>/projects/<int:pk>/songs/<int:song_pk>/remove/', views.project_remove_song, name='project_remove_song'),
    path('<str:username>/projects/<int:pk>/guests/add/', views.project_add_guest, name='project_add_guest'),
    path('<str:username>/projects/<int:pk>/guests/<int:guest_pk>/remove/', views.project_remove_guest, name='project_remove_guest'),


]