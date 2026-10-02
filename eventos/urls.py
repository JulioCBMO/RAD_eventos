from django.urls import path

from . import views

urlpatterns = [
    path("", views.EventoListView.as_view(), name="evento_lista"),
    path("eventos/novo/", views.EventoCreateView.as_view(), name="evento_criar"),
    path("eventos/meus/", views.MeusEventosView.as_view(), name="meus_eventos"),
    path("eventos/<int:pk>/", views.EventoDetailView.as_view(), name="evento_detalhe"),
    path("eventos/<int:pk>/editar/", views.EventoUpdateView.as_view(), name="evento_editar"),
    path("eventos/<int:pk>/excluir/", views.EventoDeleteView.as_view(), name="evento_excluir"),
    path("eventos/<int:pk>/painel/", views.PainelView.as_view(), name="painel"),
    path("eventos/<int:evento_pk>/atividades/nova/", views.AtividadeCreateView.as_view(), name="atividade_criar"),
    path("atividades/<int:pk>/editar/", views.AtividadeUpdateView.as_view(), name="atividade_editar"),
    path("atividades/<int:pk>/excluir/", views.AtividadeDeleteView.as_view(), name="atividade_excluir"),
    path("eventos/<int:pk>/inscrever/", views.inscrever_evento, name="inscrever_evento"),
    path("atividades/<int:pk>/inscrever/", views.inscrever_atividade, name="inscrever_atividade"),
    path("inscricoes/atividade/<int:pk>/cancelar/", views.cancelar_atividade, name="cancelar_atividade"),
    path("inscricoes/evento/<int:pk>/cancelar/", views.cancelar_evento, name="cancelar_evento"),
    path("agenda/", views.AgendaView.as_view(), name="agenda"),
]