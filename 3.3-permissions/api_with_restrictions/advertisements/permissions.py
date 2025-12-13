from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """Разрешение, позволяющее редактировать/удалять только владельцу объявления."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return obj.creator == request.user


class IsAdminOrReadOnly(BasePermission):
    """Админы могут всё, остальные только читать."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        return request.user and request.user.is_staff


class IsAdminOrOwner(BasePermission):
    """Админы могут всё, остальные - только свои объекты."""

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True

        return obj.creator == request.user