from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Checks the Keycloak roles attached by KeycloakAuthentication.
    Always use together with IsAuthenticated.
    """
    def has_permission(self, request, view):
        roles = getattr(request, "keycloak_roles", [])
        return "admin" in roles
