"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
]

schema_view = get_schema_view(
    openapi.Info(
        title="Learning Assessment API",
        default_version="v1",
        description="REST API for the Smart TV learning/assessment platform (quizzes, exams, memory games, reporting).",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


def get_full_url(request):
    scheme = request.scheme
    host = request.get_host()
    forwarded_port = request.META.get("HTTP_X_FORWARDED_PORT")

    if ":" not in host and forwarded_port:
        host = f"{host}:{forwarded_port}"

    return f"{scheme}://{host}"


@csrf_exempt
def dynamic_schema_view(request, *args, **kwargs):
    """
    Swagger UI with dynamically inferred host/scheme so it works in proxied environments.
    """
    url = get_full_url(request)
    view = get_schema_view(
        openapi.Info(
            title="Learning Assessment API",
            default_version="v1",
            description="API Docs (Swagger UI)",
        ),
        public=True,
        url=url,
        permission_classes=(permissions.AllowAny,),
    )
    return view.with_ui("swagger", cache_timeout=0)(request)


urlpatterns += [
    re_path(r"^docs/$", dynamic_schema_view, name="schema-swagger-ui"),
    re_path(r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # Common aliases
    re_path(r"^swagger\.json$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    re_path(r"^openapi\.json$", schema_view.without_ui(cache_timeout=0), name="openapi-json"),
]
