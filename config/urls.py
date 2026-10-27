from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm
from django.urls import include, path, reverse_lazy
from django.views.generic import CreateView
from rest_framework.authtoken.views import obtain_auth_token
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("contas/", include("django.contrib.auth.urls")),
    path(
        "contas/cadastro/",
        CreateView.as_view(
            form_class=UserCreationForm,
            template_name="registration/cadastro.html",
            success_url=reverse_lazy("login"),
        ),
        name="cadastro",
    ),
    # API: token, schema e documentação
    path("api/token/", obtain_auth_token, name="api-token"),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
    path("api/", include("eventos.api_urls")),
    # Site HTML existente
    path("", include("eventos.urls")),
]
