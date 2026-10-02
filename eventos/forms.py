from django import forms

from .models import Atividade, Evento


class DateTimeLocalInput(forms.DateTimeInput):
    input_type = "datetime-local"

    def __init__(self, **kwargs):
        super().__init__(format="%Y-%m-%dT%H:%M", **kwargs)


# organizador NÃO está em fields. As regras (período, fim > início, sala ocupada)
# ficam em Evento.clean() / Atividade.clean(), que o ModelForm chama sozinho.
class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ["nome", "descricao", "data_inicio", "data_fim", "inscricoes_abertas"]
        widgets = {"data_inicio": DateTimeLocalInput(), "data_fim": DateTimeLocalInput()}


# evento NÃO está em fields: a view já entrega a instância com o evento definido.
class AtividadeForm(forms.ModelForm):
    class Meta:
        model = Atividade
        fields = ["titulo", "tipo", "descricao", "responsavel", "sala", "inicio", "fim"]
        widgets = {"inicio": DateTimeLocalInput(), "fim": DateTimeLocalInput()}