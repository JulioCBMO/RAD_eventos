from django.db import transaction

from .models import Atividade, InscricaoAtividade, Sala


def conflitos_na_agenda(participante, atividade):
    """Atividades do participante, de QUALQUER evento, que se sobrepõem a `atividade`.

    A consulta parte do participante (não do evento), por isso pega conflitos
    entre eventos diferentes. Sobreposição: a1 < b2 e b1 < a2.
    """
    return Atividade.objects.filter(
        inscricoes__inscricao_evento__participante=participante,
        inicio__lt=atividade.fim,
        fim__gt=atividade.inicio,
    ).exclude(pk=atividade.pk)


def motivo_bloqueio(inscricao, atividade):
    """Devolve uma mensagem se NÃO puder inscrever; None se puder.

    Usada pela view (decisão real) e pelo template (esconder o botão).
    """
    if atividade.evento_id != inscricao.evento_id:
        return "Esta atividade não pertence ao evento da sua inscrição."
    if inscricao.inscricoes_atividade.filter(atividade=atividade).exists():
        return "Você já está inscrito nesta atividade."
    # RN1: capacidade vem da sala, contagem feita agora no banco
    if atividade.inscricoes.count() >= atividade.sala.capacidade:
        return "Esta atividade está lotada."
    # RN2: todas as atividades do participante
    conflito = conflitos_na_agenda(inscricao.participante, atividade).first()
    if conflito:
        return f"Conflito de horário com «{conflito.titulo}» ({conflito.evento})."
    return None


def inscrever_em_atividade(inscricao, atividade):
    """Retorna (ok, mensagem). Verifica e grava dentro de uma transação.

    O lock na sala serializa inscrições concorrentes na mesma atividade
    (em SQLite o select_for_update é ignorado, mas o SQLite já serializa escritas).
    """
    with transaction.atomic():
        Sala.objects.select_for_update().get(pk=atividade.sala_id)
        motivo = motivo_bloqueio(inscricao, atividade)
        if motivo:
            return False, motivo
        InscricaoAtividade.objects.create(inscricao_evento=inscricao, atividade=atividade)
    return True, f"Inscrição confirmada em «{atividade.titulo}»."