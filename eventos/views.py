from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView,
)

from . import services
from .forms import AtividadeForm, EventoForm
from .models import Atividade, Evento, InscricaoAtividade, InscricaoEvento


# ---------------------------------------------------------------- Mixin de propriedade
class DonoDoEventoMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Exige a permissão do papel E que o evento seja do usuário (propriedade).

    Não usa is_superuser: o superusuário também só mexe no que é dele.
    Autenticado sem acesso -> 403; anônimo -> tela de login.
    """

    permissao = None

    def get_evento(self):
        raise NotImplementedError

    def test_func(self):
        u = self.request.user
        return u.has_perm(self.permissao) and self.get_evento().organizador_id == u.id


# ---------------------------------------------------------------- Páginas públicas (RF3)
class EventoListView(ListView):
    model = Evento
    template_name = "eventos/evento_list.html"


class EventoDetailView(DetailView):
    model = Evento
    template_name = "eventos/evento_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        evento, user = self.object, self.request.user
        inscricao = None
        minhas = {}
        if user.is_authenticated:
            inscricao = InscricaoEvento.objects.filter(evento=evento, participante=user).first()
            if inscricao:
                minhas = {ia.atividade_id: ia for ia in inscricao.inscricoes_atividade.all()}
        linhas = []
        for a in evento.atividades.select_related("sala"):
            vagas = a.vagas_restantes
            ia = minhas.get(a.pk)
            linhas.append({
                "atividade": a,
                "vagas": vagas,
                "lotada": vagas <= 0,
                "inscricao_atividade": ia,
                # RF10: o botão só aparece se a inscrição seria aceita
                "pode_inscrever": bool(inscricao) and not ia
                and services.motivo_bloqueio(inscricao, a) is None,
            })
        dono = user.is_authenticated and evento.organizador_id == user.id
        ctx.update({
            "linhas": linhas,
            "inscricao": inscricao,
            "pode_editar": dono and user.has_perm("eventos.change_evento"),
            "pode_adicionar_atividade": dono and user.has_perm("eventos.add_atividade"),
        })
        return ctx


# ---------------------------------------------------------------- CRUD do organizador (RF4)
class EventoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Evento
    form_class = EventoForm
    permission_required = "eventos.add_evento"
    template_name = "eventos/evento_form.html"

    def form_valid(self, form):
        form.instance.organizador = self.request.user  # nunca vem do formulário
        return super().form_valid(form)


class EventoUpdateView(DonoDoEventoMixin, UpdateView):
    model = Evento
    form_class = EventoForm
    permissao = "eventos.change_evento"
    template_name = "eventos/evento_form.html"

    def get_evento(self):
        return self.get_object()


class EventoDeleteView(DonoDoEventoMixin, DeleteView):
    model = Evento
    permissao = "eventos.delete_evento"
    template_name = "eventos/confirm_delete.html"
    success_url = reverse_lazy("evento_lista")

    def get_evento(self):
        return self.get_object()


class MeusEventosView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = "eventos.add_evento"
    template_name = "eventos/meus_eventos.html"

    def get_queryset(self):
        return Evento.objects.filter(organizador=self.request.user)


class AtividadeCreateView(DonoDoEventoMixin, CreateView):
    model = Atividade
    form_class = AtividadeForm
    permissao = "eventos.add_atividade"
    template_name = "eventos/atividade_form.html"

    def get_evento(self):
        if not hasattr(self, "_evento"):
            self._evento = get_object_or_404(Evento, pk=self.kwargs["evento_pk"])
        return self._evento

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["instance"] = Atividade(evento=self.get_evento())
        return kw

    def get_context_data(self, **kwargs):
        return super().get_context_data(evento=self.get_evento(), **kwargs)

    def get_success_url(self):
        return reverse("evento_detalhe", args=[self.get_evento().pk])


class AtividadeUpdateView(DonoDoEventoMixin, UpdateView):
    model = Atividade
    form_class = AtividadeForm
    permissao = "eventos.change_atividade"
    template_name = "eventos/atividade_form.html"

    def get_evento(self):
        return self.get_object().evento

    def get_context_data(self, **kwargs):
        return super().get_context_data(evento=self.object.evento, **kwargs)

    def get_success_url(self):
        return reverse("evento_detalhe", args=[self.object.evento_id])


class AtividadeDeleteView(DonoDoEventoMixin, DeleteView):
    model = Atividade
    permissao = "eventos.delete_atividade"
    template_name = "eventos/confirm_delete.html"

    def get_evento(self):
        return self.get_object().evento

    def get_success_url(self):
        return reverse("evento_detalhe", args=[self.object.evento_id])


# ---------------------------------------------------------------- Painel (RF9)
class PainelView(DonoDoEventoMixin, DetailView):
    model = Evento
    permissao = "eventos.change_evento"
    template_name = "eventos/painel.html"

    def get_evento(self):
        return self.get_object()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["atividades"] = self.object.atividades.select_related("sala").prefetch_related(
            "inscricoes__inscricao_evento__participante"
        )
        return ctx


# ---------------------------------------------------------------- Ações (somente POST)
def _voltar(request, padrao):
    destino = request.POST.get("next", "")
    if destino and url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}):
        return redirect(destino)
    return redirect(padrao)


@login_required
@require_POST
def inscrever_evento(request, pk):  # RF5
    evento = get_object_or_404(Evento, pk=pk)
    if not evento.inscricoes_abertas:
        messages.error(request, "Este evento não aceita novas inscrições.")
    elif InscricaoEvento.objects.filter(evento=evento, participante=request.user).exists():
        messages.error(request, "Você já está inscrito neste evento.")
    else:
        try:
            InscricaoEvento.objects.create(evento=evento, participante=request.user)
            messages.success(request, f"Inscrição confirmada em «{evento.nome}».")
        except IntegrityError:
            messages.error(request, "Você já está inscrito neste evento.")
    return redirect("evento_detalhe", pk=evento.pk)


@login_required
@require_POST
def inscrever_atividade(request, pk):  # RF6
    atividade = get_object_or_404(Atividade.objects.select_related("evento", "sala"), pk=pk)
    inscricao = InscricaoEvento.objects.filter(
        evento=atividade.evento, participante=request.user
    ).first()
    if inscricao is None:  # RN4
        messages.error(request, "Inscreva-se no evento antes de escolher atividades.")
    else:
        ok, msg = services.inscrever_em_atividade(inscricao, atividade)
        (messages.success if ok else messages.error)(request, msg)
    return redirect("evento_detalhe", pk=atividade.evento_id)


@login_required
@require_POST
def cancelar_atividade(request, pk):  # RF7 (uma atividade)
    ia = get_object_or_404(InscricaoAtividade.objects.select_related("inscricao_evento"), pk=pk)
    if ia.inscricao_evento.participante_id != request.user.id:
        raise PermissionDenied
    ia.delete()
    messages.success(request, "Inscrição na atividade cancelada.")
    return _voltar(request, "agenda")


@login_required
@require_POST
def cancelar_evento(request, pk):  # RF7 + RN5 (cascata pelo on_delete)
    inscricao = get_object_or_404(InscricaoEvento, pk=pk)
    if inscricao.participante_id != request.user.id:
        raise PermissionDenied
    inscricao.delete()
    messages.success(request, "Inscrição no evento cancelada, junto com as atividades.")
    return _voltar(request, "agenda")


# ---------------------------------------------------------------- Agenda (RF8)
class AgendaView(LoginRequiredMixin, TemplateView):
    template_name = "eventos/agenda.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user  # só as inscrições de quem abriu
        ctx["itens"] = (
            InscricaoAtividade.objects.filter(inscricao_evento__participante=u)
            .select_related("atividade__sala", "atividade__evento")
            .order_by("atividade__inicio")
        )
        ctx["inscricoes"] = InscricaoEvento.objects.filter(participante=u).select_related("evento")
        return ctx