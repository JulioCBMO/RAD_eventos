from django.contrib import admin
from .models import Atividade, Evento, InscricaoAtividade, InscricaoEvento, Sala

@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ("nome", "bloco", "capacidade")
    search_fields = ("nome", "bloco")
    list_filter = ("bloco",)

class AtividadeIncline(admin.TabularInline):
    model = Atividade
    extra = 0


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ("nome", "data_inicio", "data_fim", "inscricoes_abertas", "organizador")
    search_fields = ("nome", "organizador__username")
    list_filter = ("data_inicio", "inscricoes_abertas")
    readonly_fields = ("organizador",)
    inlines = [AtividadeIncline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.organizador = request.user
        super().save_model(request, obj, form, change)

@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "evento", "sala", "inicio", "fim", "responsavel")
    list_filter = ("tipo", "evento", "sala")
    search_fields = ("titulo", "responsavel", "evento__nome")


@admin.register(InscricaoEvento)
class InscricaoEventoAdmin(admin.ModelAdmin):
    list_display = ("participante", "evento", "data")
    list_filter = ("evento",)
    search_fields = ("participante__username", "evento__nome")
    readonly_fields = ("participante",)
 
    def save_model(self, request, obj, form, change):
        if not change:
            obj.participante = request.user
        super().save_model(request, obj, form, change)

@admin.register(InscricaoAtividade)
class InscricaoAtividadeAdmin(admin.ModelAdmin):
    list_display = ("inscricao_evento", "atividade", "data")
    list_filter = ("atividade__evento", "atividade")
    search_fields = ("inscricao_evento__participante__username", "atividade__titulo")