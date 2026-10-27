"""Uso: python manage.py popular   (pode rodar mais de uma vez)"""
from datetime import datetime

from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware

from eventos.models import Atividade, Evento, Sala

SENHA = "senha123"


def dt(dia, hora):
    return make_aware(datetime(2026, 11, dia, hora, 0))


class Command(BaseCommand):
    help = "Cria usuários, grupo Organizadores, salas, eventos e atividades de teste"

    def handle(self, *args, **options):
        # --- Grupo Organizadores (papel por permissão, não por is_superuser)
        grupo, _ = Group.objects.get_or_create(name="Organizadores")
        perms = Permission.objects.filter(
            content_type__app_label="eventos",
            codename__in=[
                "add_evento", "change_evento", "delete_evento",
                "add_atividade", "change_atividade", "delete_atividade",
            ],
        )
        grupo.permissions.set(perms)

        # --- Usuários (set_password via create_user, nunca direto no campo)
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@ifpb.edu.br", SENHA)
        usuarios = {}
        for nome in ["organizador2", "organizador3", "participante4", "participante5"]:
            u, criado = User.objects.get_or_create(username=nome)
            if criado:
                u.set_password(SENHA)
                u.save()
            usuarios[nome] = u
        usuarios["organizador2"].groups.add(grupo)
        usuarios["organizador3"].groups.add(grupo)

        # --- Salas
        aud, _ = Sala.objects.get_or_create(nome="Auditório", defaults={"bloco": "A", "capacidade": 100})
        lab, _ = Sala.objects.get_or_create(nome="Laboratório 1", defaults={"bloco": "B", "capacidade": 30})
        peq, _ = Sala.objects.get_or_create(nome="Sala Pequena", defaults={"bloco": "B", "capacidade": 2})

        # --- Eventos com períodos que se cruzam (10-12/nov e 11-13/nov)
        ev1, _ = Evento.objects.get_or_create(
            nome="Semana Acadêmica",
            defaults={"descricao": "Semana Acadêmica de SI", "data_inicio": dt(10, 8),
                      "data_fim": dt(12, 18), "organizador": usuarios["organizador2"]},
        )
        ev2, _ = Evento.objects.get_or_create(
            nome="Jornada Científica",
            defaults={"descricao": "Jornada de iniciação científica", "data_inicio": dt(11, 8),
                      "data_fim": dt(13, 18), "organizador": usuarios["organizador3"]},
        )

        def ativ(evento, titulo, tipo, sala, ini, fim, resp):
            Atividade.objects.get_or_create(
                evento=evento, titulo=titulo,
                defaults={"tipo": tipo, "sala": sala, "inicio": ini, "fim": fim,
                          "responsavel": resp, "descricao": titulo},
            )

        T = Atividade.Tipo
        # Mesma sala (Auditório), horários que NÃO se cruzam
        ativ(ev1, "Palestra de abertura", T.PALESTRA, aud, dt(11, 9), dt(11, 10), "Profa. Ana")
        ativ(ev1, "Palestra sobre Django", T.PALESTRA, aud, dt(11, 14), dt(11, 16), "Prof. Bruno")
        # Mesmo horário (11/nov 9h-11h), salas distintas, eventos diferentes
        ativ(ev2, "Treinamento de Git", T.TREINAMENTO, lab, dt(11, 9), dt(11, 11), "Carlos")
        # Sala de capacidade 2
        ativ(ev1, "Oficina de UX (2 vagas)", T.TREINAMENTO, peq, dt(12, 9), dt(12, 11), "Dra. Débora")
        ativ(ev2, "Apresentação de pôsteres", T.APRESENTACAO, aud, dt(12, 14), dt(12, 17), "Alunos de IC")

        self.stdout.write(self.style.SUCCESS(f"Dados criados. Senha de todas as contas: {SENHA}"))