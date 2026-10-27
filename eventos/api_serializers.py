from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .models import Sala, Evento, Atividade, InscricaoEvento, InscricaoAtividade
from . import services


class SalaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sala
        fields = ["id", "nome", "bloco", "capacidade"]


class AtividadeSerializer(serializers.ModelSerializer):
    sala_nome = serializers.CharField(source="sala.nome", read_only=True)
    vagas_restantes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Atividade
        fields = [
            "id", "evento", "titulo", "tipo", "descricao", "responsavel",
            "sala", "sala_nome", "inicio", "fim", "vagas_restantes",
        ]

    def validate(self, attrs):
        instance = self.instance or Atividade()
        for key, value in attrs.items():
            setattr(instance, key, value)
        # Em atualização, preservar os campos que não vieram no PATCH.
        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            if hasattr(exc, "message_dict"):
                raise serializers.ValidationError(exc.message_dict)
            raise serializers.ValidationError({"detail": exc.messages})
        request = self.context.get("request")
        evento = attrs.get("evento", getattr(instance, "evento", None))
        if request and request.user.is_authenticated and evento and evento.organizador_id != request.user.id:
            raise serializers.ValidationError({"evento": "Você só pode criar atividades em eventos que organiza."})
        return attrs


class EventoSerializer(serializers.ModelSerializer):
    organizador = serializers.PrimaryKeyRelatedField(read_only=True)
    organizador_nome = serializers.CharField(source="organizador.username", read_only=True)

    class Meta:
        model = Evento
        fields = ["id", "nome", "descricao", "data_inicio", "data_fim",
                  "inscricoes_abertas", "organizador", "organizador_nome"]
        read_only_fields = ["organizador"]

    def validate(self, attrs):
        instance = self.instance or Evento(organizador=self.context["request"].user)
        for key, value in attrs.items():
            setattr(instance, key, value)
        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            if hasattr(exc, "message_dict"):
                raise serializers.ValidationError(exc.message_dict)
            raise serializers.ValidationError({"detail": exc.messages})
        return attrs


class ProgramacaoAtividadeSerializer(serializers.ModelSerializer):
    sala = serializers.CharField(source="sala.nome", read_only=True)
    vagas_restantes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Atividade
        fields = ["id", "titulo", "tipo", "descricao", "responsavel",
                  "sala", "inicio", "fim", "vagas_restantes"]


class ProgramacaoEventoSerializer(serializers.ModelSerializer):
    organizador = serializers.CharField(source="organizador.username", read_only=True)
    atividades = ProgramacaoAtividadeSerializer(many=True, read_only=True)

    class Meta:
        model = Evento
        fields = ["id", "nome", "descricao", "organizador", "data_inicio",
                  "data_fim", "atividades"]


class InscricaoEventoSerializer(serializers.ModelSerializer):
    evento = serializers.PrimaryKeyRelatedField(queryset=Evento.objects.all())

    class Meta:
        model = InscricaoEvento
        fields = ["id", "evento", "data"]
        read_only_fields = ["id", "data"]

    def validate_evento(self, evento):
        if not evento.inscricoes_abertas:
            raise serializers.ValidationError("Este evento não aceita novas inscrições.")
        return evento

    def create(self, validated_data):
        participante = self.context["request"].user
        evento = validated_data["evento"]
        if InscricaoEvento.objects.filter(evento=evento, participante=participante).exists():
            raise serializers.ValidationError({"evento": "Você já está inscrito neste evento."})
        return InscricaoEvento.objects.create(evento=evento, participante=participante)


class InscricaoAtividadeSerializer(serializers.Serializer):
    atividade = serializers.PrimaryKeyRelatedField(
        queryset=Atividade.objects.select_related("evento", "sala"),
    )

    def create(self, validated_data):
        participante = self.context["request"].user
        atividade = validated_data["atividade"]
        inscricao = InscricaoEvento.objects.filter(
            evento=atividade.evento, participante=participante
        ).first()
        if inscricao is None:
            raise serializers.ValidationError({"detail": "Inscreva-se no evento antes de escolher atividades."})
        ok, mensagem = services.inscrever_em_atividade(inscricao, atividade)
        if not ok:
            raise serializers.ValidationError({"detail": mensagem})
        return InscricaoAtividade.objects.get(inscricao_evento=inscricao, atividade=atividade)


class InscricaoAtividadeReadSerializer(serializers.ModelSerializer):
    evento = serializers.CharField(source="atividade.evento.nome", read_only=True)
    atividade_titulo = serializers.CharField(source="atividade.titulo", read_only=True)
    sala = serializers.CharField(source="atividade.sala.nome", read_only=True)
    inicio = serializers.DateTimeField(source="atividade.inicio", read_only=True)
    fim = serializers.DateTimeField(source="atividade.fim", read_only=True)

    class Meta:
        model = InscricaoAtividade
        fields = ["id", "evento", "atividade_titulo", "sala", "inicio", "fim"]
