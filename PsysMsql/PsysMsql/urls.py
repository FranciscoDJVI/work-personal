from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("psysmysql.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("users.urls")),
    # API v1 endpoints
    path("api/v1/", include("psysmysql.api.urls")),
]
