from django.urls import path

from . import views

urlpatterns = [
    # ex: /admin/secondapp/
    path("admin/secondapp/", views.index, name="index"),
    # ex: /admin/secondapp/2023-10-01/
    path("admin/secondapp/<str:rehearsal_date>/", views.detail, name="detail"),
    # ex: /admin/secondapp/2023-10-01/results/
    #path("admin/secondapp/<str:rehearsal_date>/results/", views.results, name="results"),
    # ex: /admin/secondapp/2023-10-01/vote/
    path("admin/secondapp/<str:rehearsal_date>/vote/", views.vote, name="vote"),

]