"""
Custom DRF authentication that validates Keycloak JWT tokens.
Django does NOT store passwords — Keycloak owns auth entirely.
"""
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from keycloak import KeycloakOpenID
from apps.users.models import User


def _get_keycloak():
    return KeycloakOpenID(
        server_url=settings.KEYCLOAK_URL + "/",
        realm_name=settings.KEYCLOAK_REALM,
        client_id=settings.KEYCLOAK_CLIENT_ID,
        verify=False,  # set True in prod with proper cert
    )


class KeycloakAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ", 1)[1]

        try:
            keycloak = _get_keycloak()
            userinfo = keycloak.introspect(token)
        except Exception as e:
            raise AuthenticationFailed(f"Token validation failed: {e}")

        if not userinfo.get("active"):
            raise AuthenticationFailed("Token is inactive or expired.")

        # Sync user to local DB — create on first login
        user, _ = User.objects.get_or_create(
            email=userinfo["email"],
            defaults={
                "full_name": userinfo.get("name", ""),
                "is_active": True,
            },
        )

        # Attach Keycloak roles so IsAdmin permission can read them
        request.keycloak_roles = userinfo.get("realm_access", {}).get("roles", [])

        return (user, token)
