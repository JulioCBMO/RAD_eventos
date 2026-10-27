from datetime import timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from .models import Sala, Evento, Atividade, InscricaoEvento, InscricaoAtividade
from .services import inscrever_em_atividade


class RegrasCompartilhadasTests(TestCase):
    def setUp(self):
        agora = timezone.now().replace(second=0, microsecond=0)
        self.organizador = User.objects.create_user(username="org", password="senha123")
        self.p1 = User.objects.create_user(username="p1", password="senha123")
        self.p2 = User.objects.create_user(username="p2", password="senha123")
        self.sala = Sala.objects.create(nome="Sala teste", bloco="A", capacidade=1)
        self.evento = Evento.objects.create(
            nome="Evento teste", descricao="", data_inicio=agora,
            data_fim=agora + timedelta(days=2), organizador=self.organizador,
        )
        self.atividade = Atividade.objects.create(
            evento=self.evento, titulo="Atividade A", tipo=Atividade.Tipo.PALESTRA,
            descricao="", responsavel="Teste", sala=self.sala,
            inicio=agora + timedelta(hours=1), fim=agora + timedelta(hours=2),
        )
        self.inscricao1 = InscricaoEvento.objects.create(evento=self.evento, participante=self.p1)
        self.inscricao2 = InscricaoEvento.objects.create(evento=self.evento, participante=self.p2)

    def test_capacidade_rejeita_segunda_inscricao(self):
        ok, _ = inscrever_em_atividade(self.inscricao1, self.atividade)
        self.assertTrue(ok)
        ok, mensagem = inscrever_em_atividade(self.inscricao2, self.atividade)
        self.assertFalse(ok)
        self.assertIn("lotada", mensagem)

    def test_conflito_de_sala_rejeitado_no_modelo(self):
        outra = Atividade(
            evento=self.evento, titulo="Atividade B", tipo=Atividade.Tipo.PALESTRA,
            descricao="", responsavel="Teste", sala=self.sala,
            inicio=self.atividade.inicio + timedelta(minutes=30),
            fim=self.atividade.fim + timedelta(minutes=30),
        )
        with self.assertRaises(ValidationError):
            outra.full_clean()

    def test_cancelar_inscricao_evento_remove_escolhas(self):
        InscricaoAtividade.objects.create(inscricao_evento=self.inscricao1, atividade=self.atividade)
        self.inscricao1.delete()
        self.assertFalse(InscricaoAtividade.objects.filter(inscricao_evento_id=self.inscricao1.pk).exists())


class APITests(TestCase):
    def setUp(self):
        agora = timezone.now().replace(second=0, microsecond=0)
        self.organizador = User.objects.create_user(username="organizador", password="senha123")
        self.participante = User.objects.create_user(username="participante", password="senha123")
        self.sala = Sala.objects.create(nome="Auditório API", capacidade=10)
        self.evento = Evento.objects.create(
            nome="Evento API", data_inicio=agora, data_fim=agora + timedelta(days=1),
            organizador=self.organizador,
        )
        self.atividade = Atividade.objects.create(
            evento=self.evento, titulo="Palestra API", tipo=Atividade.Tipo.PALESTRA,
            responsavel="Equipe", sala=self.sala,
            inicio=agora + timedelta(hours=1), fim=agora + timedelta(hours=2),
        )
        self.token = Token.objects.create(user=self.participante)
        self.client = APIClient()

    def test_programacao_publica_inclui_sala_e_vagas(self):
        response = self.client.get(f"/api/eventos/{self.evento.pk}/programacao/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["atividades"][0]["sala"], self.sala.nome)
        self.assertEqual(response.data["atividades"][0]["vagas_restantes"], 10)

    def test_agenda_exige_token(self):
        self.assertEqual(self.client.get("/api/minha-agenda/").status_code, 401)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.assertEqual(self.client.get("/api/minha-agenda/").status_code, 200)

    def test_inscricao_atividade_sem_inscricao_evento_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(
            "/api/inscricoes/atividade/", {"atividade": self.atividade.pk}, format="json"
        )
        self.assertEqual(response.status_code, 400)
