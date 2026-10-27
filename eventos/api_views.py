from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Sala, Evento, Atividade, InscricaoEvento, InscricaoAtividade
from .api_serializers import (
    SalaSerializer, EventoSerializer, AtividadeSerializer,
    ProgramacaoEventoSerializer, InscricaoEventoSerializer,
    InscricaoAtividadeSerializer, InscricaoAtividadeReadSerializer,
)
from .api_permissions import IsOrganizerOfObject


class EventoViewSet(viewsets.ModelViewSet):
    serializer_class = EventoSerializer
    queryset = Evento.objects.select_related("organizador").all()

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsOrganizerOfObject()]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action in ("list", "retrieve"):
            return qs
        return qs.filter(organizador=self.request.user)

    def perform_create(self, serializer):
        serializer.save(organizador=self.request.user)


class AtividadeViewSet(viewsets.ModelViewSet):
    serializer_class = AtividadeSerializer
    queryset = Atividade.objects.select_related("evento", "sala", "evento__organizador").all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["titulo", "descricao"]
    ordering_fields = ["inicio"]
    ordering = ["inicio"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsOrganizerOfObject()]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action in ("list", "retrieve"):
            return qs
        return qs.filter(evento__organizador=self.request.user)

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()


class SalaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sala.objects.all()
    serializer_class = SalaSerializer
    permission_classes = [permissions.AllowAny()]


@extend_schema(responses=ProgramacaoEventoSerializer)
@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def programacao_evento(request, pk):
    evento = get_object_or_404(
        Evento.objects.prefetch_related("atividades__sala"), pk=pk
    )
    return Response(ProgramacaoEventoSerializer(evento).data)


@extend_schema(request=InscricaoEventoSerializer, responses={201: InscricaoEventoSerializer})
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def inscrever_evento(request):
    serializer = InscricaoEventoSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    obj = serializer.save()
    return Response(InscricaoEventoSerializer(obj).data, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
@permission_classes([permissions.IsAuthenticated])
def cancelar_inscricao_evento(request, pk):
    inscricao = get_object_or_404(InscricaoEvento, pk=pk)
    if inscricao.participante_id != request.user.id:
        raise PermissionDenied("Você só pode cancelar sua própria inscrição.")
    inscricao.delete()  # CASCADE cancela as inscrições nas atividades
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(request=InscricaoAtividadeSerializer, responses={201: InscricaoAtividadeReadSerializer})
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def inscrever_atividade(request):
    serializer = InscricaoAtividadeSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    obj = serializer.save()
    return Response(InscricaoAtividadeReadSerializer(obj).data, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
@permission_classes([permissions.IsAuthenticated])
def cancelar_inscricao_atividade(request, pk):
    inscricao = get_object_or_404(
        InscricaoAtividade.objects.select_related("inscricao_evento"), pk=pk
    )
    if inscricao.inscricao_evento.participante_id != request.user.id:
        raise PermissionDenied("Você só pode cancelar sua própria inscrição.")
    inscricao.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(responses=InscricaoAtividadeReadSerializer(many=True))
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def minha_agenda(request):
    itens = InscricaoAtividade.objects.filter(
        inscricao_evento__participante=request.user
    ).select_related("atividade__evento", "atividade__sala").order_by("atividade__inicio")
    return Response(InscricaoAtividadeReadSerializer(itens, many=True).data)
