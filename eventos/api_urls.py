from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .api_views import (
    EventoViewSet, AtividadeViewSet, SalaViewSet, programacao_evento,
    inscrever_evento, cancelar_inscricao_evento, inscrever_atividade,
    cancelar_inscricao_atividade, minha_agenda,
)

router = DefaultRouter()
router.register("eventos", EventoViewSet, basename="api-evento")
router.register("atividades", AtividadeViewSet, basename="api-atividade")
router.register("salas", SalaViewSet, basename="api-sala")

urlpatterns = [
    path("", include(router.urls)),
    path("eventos/<int:pk>/programacao/", programacao_evento, name="api-programacao-evento"),
    path("inscricoes/evento/", inscrever_evento, name="api-inscrever-evento"),
    path("inscricoes/evento/<int:pk>/cancelar/", cancelar_inscricao_evento, name="api-cancelar-evento"),
    path("inscricoes/atividade/", inscrever_atividade, name="api-inscrever-atividade"),
    path("inscricoes/atividade/<int:pk>/cancelar/", cancelar_inscricao_atividade, name="api-cancelar-atividade"),
    path("minha-agenda/", minha_agenda, name="api-minha-agenda"),
]
