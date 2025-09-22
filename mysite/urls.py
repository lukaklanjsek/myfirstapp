"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.views.decorators.cache import cache_page
from django.views.i18n import JavaScriptCatalog

urlpatterns = [
    path("admin/", admin.site.urls),
    path("polls/", include("polls.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path('jsi18n/', cache_page(3600)(JavaScriptCatalog.as_view(packages=['formset'])), name='javascript-catalog'),
    path("select2/", include("django_select2.urls")),
    path("", include("secondapp.urls", namespace="secondapp")),

]



from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns += staticfiles_urlpatterns()

