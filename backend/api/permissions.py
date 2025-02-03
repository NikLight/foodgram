from rest_framework.permissions import BasePermission


class IsAuthorOrAdmin(BasePermission):
    """
    Разрешение, позволяющее обновлять или удалять объект только автору или администратору.
    """
    def has_object_permission(self, request, view, obj):
        return request.user == obj.author or request.user.is_staff
