from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Sala(models.Model):
    nome = models.CharField(max_length=100)
    bloco = models.CharField(max_length=50, blank=True)
    capacidade = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["bloco", "nome"]

    def __str__(self):
        return f"{self.nome} ({self.capacidade} lugares)"


class Evento(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    inscricoes_abertas = models.BooleanField(default=True)
    # Preenchido pelo sistema (view / Admin), nunca pelo formulário
    organizador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="eventos_organizados",
        editable=False,
    )

    class Meta:
        ordering = ["data_inicio"]

    def __str__(self):
        return self.nome

    def clean(self):
        super().clean()
        if not (self.data_inicio and self.data_fim):
            return
        if self.data_fim < self.data_inicio:
            raise ValidationError("O fim do evento não pode ser antes do início.")
        if self.pk and self.atividades.filter(
            models.Q(inicio__lt=self.data_inicio) | models.Q(fim__gt=self.data_fim)
        ).exists():
            raise ValidationError(
                "Há atividades fora do novo período. Ajuste-as antes de mudar as datas."
            )


class Atividade(models.Model):
    class Tipo(models.TextChoices):
        PALESTRA = "PAL", "Palestra"
        TREINAMENTO = "TRE", "Treinamento"
        APRESENTACAO = "APR", "Apresentação"

    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, related_name="atividades"
    )
    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=3, choices=Tipo.choices)
    descricao = models.TextField(blank=True)
    responsavel = models.CharField(max_length=150)
    # PROTECT: não apaga uma sala que ainda tem atividades
    sala = models.ForeignKey(
        Sala, on_delete=models.PROTECT, related_name="atividades"
    )
    inicio = models.DateTimeField()
    fim = models.DateTimeField()

    class Meta:
        ordering = ["inicio"]
        verbose_name_plural = "atividades"

    def __str__(self):
        return self.titulo

    @property
    def vagas_restantes(self):
        # Sempre calculado a partir do banco (restrição 5)
        return self.sala.capacidade - self.inscricoes.count()

    def clean(self):
        super().clean()
        if not (self.inicio and self.fim):
            return
        if self.fim <= self.inicio:
            raise ValidationError("O fim da atividade deve ser depois do início.")
        if self.evento_id and (
            self.inicio < self.evento.data_inicio or self.fim > self.evento.data_fim
        ):
            raise ValidationError(
                "A atividade deve acontecer dentro do período do evento."
            )
        if self.sala_id:
            # RN3: dois intervalos [a1,a2) e [b1,b2) se sobrepõem se a1 < b2 e b1 < a2.
            # Cobre início dentro, fim dentro, contém e está contido.
            conflito = (
                Atividade.objects.filter(
                    sala_id=self.sala_id, inicio__lt=self.fim, fim__gt=self.inicio
                )
                .exclude(pk=self.pk)
                .first()
            )
            if conflito:
                raise ValidationError(
                    f"A sala já está ocupada por «{conflito.titulo}» nesse horário."
                )


class InscricaoEvento(models.Model):
    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, related_name="inscricoes"
    )
    # Preenchido pelo sistema, nunca pelo formulário
    participante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inscricoes_evento",
        editable=False,
    )
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "participante"],
                name="unica_inscricao_por_evento",
            )
        ]
        verbose_name = "inscrição no evento"
        verbose_name_plural = "inscrições em eventos"

    def __str__(self):
        return f"{self.participante} em {self.evento}"


class InscricaoAtividade(models.Model):
    # Liga à inscrição no evento (e não direto ao usuário):
    #  - RN4: só existe se houver inscrição no evento
    #  - RN5: CASCADE remove as atividades ao cancelar o evento
    inscricao_evento = models.ForeignKey(
        InscricaoEvento,
        on_delete=models.CASCADE,
        related_name="inscricoes_atividade",
    )
    atividade = models.ForeignKey(
        Atividade, on_delete=models.CASCADE, related_name="inscricoes"
    )
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["inscricao_evento", "atividade"],
                name="unica_inscricao_por_atividade",
            )
        ]
        verbose_name = "inscrição na atividade"
        verbose_name_plural = "inscrições em atividades"

    def __str__(self):
        return f"{self.inscricao_evento.participante} em {self.atividade}"