from django.contrib import admin
from django.urls import path, include

import psysmysql.views

urlpatterns = [
    path("app/", include("psysmysql.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/", include("users.urls")),
]
