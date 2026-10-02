from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm
from django.urls import include, path, reverse_lazy
from django.views.generic import CreateView

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
    path("", include("eventos.urls")),
]