from django.urls import path

from . import views

urlpatterns = [

     path("", views.IndexView.as_view(), name="index"),

     path("rehearsal", views.IndexRehearsalView.as_view(), name="index_rehearsal"),
     path("rehearsal/<int:rehearsal_id>/", views.DetailRehearsalView.as_view(), name="detail_rehearsal"),

     path("singer", views.IndexSingerView.as_view(), name="index_singers"),
     #path("singer_inactive", views.index_singers_inactive, name="index_singers_inactive"),
     path("singer/<int:singer_id>", views.DetailSingerView.as_view(), name="detail_singer"),




    # ex: /admin/secondapp/2023-10-01/
    # path("admin/secondapp/<str:rehearsal_date>/", views.detail, name="detail"),
    # ex: /admin/secondapp/2023-10-01/results/
    # path("admin/secondapp/<str:rehearsal_date>/results/", views.results, name="results"),
    # ex: /admin/secondapp/2023-10-01/vote/
    # path("admin/secondapp/<str:rehearsal_date>/vote/", views.vote, name="vote"),

]