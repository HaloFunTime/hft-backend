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
from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token

router = routers.DefaultRouter()

admin.site.site_header = "Staff Portal"
admin.site.site_title = "HaloFunTime Backend"
admin.site.site_url = "/docs"
admin.site.index_title = "Database Tables by App"
admin.site.empty_value_display = "NULL"

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
    path("intern/", include("apps.intern.urls")),
    path("ping/", include("apps.ping.urls")),
    path("reputation/", include("apps.reputation.urls")),
    path("series/", include("apps.series.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
