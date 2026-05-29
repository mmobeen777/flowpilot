"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path, include

ROOT_URL = settings.APP_CONTEXT_ROOT

APP_VERSION1 = "/v1"
URL_USERS = APP_VERSION1 + "/users"
URL_INVITATION = APP_VERSION1 + "/invitation"
URL_API_KEY = APP_VERSION1 + "/key"


urlpatterns = [
    path('admin/', admin.site.urls),
    path(ROOT_URL + URL_USERS, include("apps.user.api.urls")),
    path(ROOT_URL + URL_INVITATION, include("apps.invitations.api.urls")),
    path(ROOT_URL + URL_API_KEY, include("apps.apikeys.api.urls")),
]
