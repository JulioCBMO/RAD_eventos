from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOrganizerOfObject(BasePermission):
    """Escrita só é permitida ao organizador do evento/atividade."""
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        evento = getattr(obj, "evento", obj)
        return evento.organizador_id == request.user.id
