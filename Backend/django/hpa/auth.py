"""
Custom DRF authentication that validates Keycloak JWT tokens.
Django does NOT store passwords — Keycloak owns auth entirely.
"""
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from keycloak import KeycloakOpenID, KeycloakAdmin, KeycloakOpenIDConnection
from apps.users.models import User


def _get_keycloak():
    return KeycloakOpenID(
        server_url=settings.KEYCLOAK_URL + "/",
        realm_name=settings.KEYCLOAK_REALM,
        client_id=settings.KEYCLOAK_CLIENT_ID,
        client_secret_key=settings.KEYCLOAK_CLIENT_SECRET,
        verify=False,
    )


def get_keycloak_openid():
    return _get_keycloak()


def get_keycloak_admin():
    connection = KeycloakOpenIDConnection(
        server_url=settings.KEYCLOAK_URL + "/",
        realm_name=settings.KEYCLOAK_REALM,
        client_id=settings.KEYCLOAK_CLIENT_ID,
        client_secret_key=settings.KEYCLOAK_CLIENT_SECRET,
        grant_type="client_credentials",
        verify=False,
    )
    return KeycloakAdmin(connection=connection)


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

        roles = userinfo.get("realm_access", {}).get("roles", [])
        kc_role = "admin" if "admin" in roles else "user"

        user, _ = User.objects.get_or_create(
            id=userinfo["sub"],
            defaults={
                "email": userinfo.get("email", ""),
                "full_name": userinfo.get("name", ""),
                "is_active": True,
                "role": kc_role,
            },
        )

        if user.role != kc_role:
            user.role = kc_role
            user.save(update_fields=["role"])

        request.keycloak_roles = roles

        return (user, token)
