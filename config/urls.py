"""api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from http import HTTPStatus
from typing import Any

from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import routers, views
from rest_framework.authtoken.views import obtain_auth_token

router = routers.DefaultRouter()

admin.site.site_header = "Staff Portal"
admin.site.site_title = "HaloFunTime Backend"
admin.site.site_url = "/docs"
admin.site.index_title = "Database Tables by App"
admin.site.empty_value_display = "NULL"


def root_exception_handler(exc: Exception, context: dict[str, Any]) -> views.Response:
    # Call DRF's default exception handler first to get the standard error response
    response = views.exception_handler(exc, context)

    if response is not None:
        # Use the descriptions from the HTTPStatus class as the error message
        http_code_to_message = {v.value: v.description for v in HTTPStatus}

        error_payload = {
            "error": {
                "status_code": 0,
                "message": "",
                "details": [],
            }
        }
        error = error_payload["error"]
        status_code = response.status_code

        error["status_code"] = status_code
        error["message"] = http_code_to_message[status_code]
        error["details"] = response.data
        response.data = error_payload
    return response


urlpatterns = [
    path("", include(router.urls)),
    path("staff/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("get-bearer-token/", obtain_auth_token, name="bearer-token"),
    # Import urls from /apps here:
    path("discord/", include("apps.discord.urls")),
    path("halo-infinite/", include("apps.halo_infinite.urls")),
    path("intern/", include("apps.intern.urls")),
    path("link/", include("apps.link.urls")),
    path("ping/", include("apps.ping.urls")),
    path("reputation/", include("apps.reputation.urls")),
    path("series/", include("apps.series.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
