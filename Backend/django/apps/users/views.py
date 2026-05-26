from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from keycloak.exceptions import KeycloakPostError, KeycloakAuthenticationError

from .models import User
from .serializers import (
      UserSerializer,
      UserUpdateSerializer,
      AdminUserCreateSerializer,
      AdminUserUpdateSerializer,
      RegisterSerializer,
      LoginSerializer,
      RefreshSerializer,
      TotalUsersSerializer,
)
from apps.common.search import SearchSerializer, apply_search, paginated_response
from hpa.permissions import IsAdmin
from hpa.auth import get_keycloak_admin, get_keycloak_openid


class MeView(APIView):
    """GET/PATCH /api/users/me/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        """[Profile] Editeaza Profil"""
        serializer = UserUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSearchView(APIView):
    """POST /api/users/search/  — admin: paginated user list with filters/sorters"""
    permission_classes = [IsAuthenticated, IsAdmin]

    ALLOWED_EQ = {"role", "is_active"}
    ALLOWED_CONTAINS = {"email", "full_name"}
    ALLOWED_SORT = {"full_name", "email", "created_date", "role", "is_active"}

    def post(self, request):
        search = SearchSerializer(data=request.data)
        search.is_valid(raise_exception=True)
        qs = apply_search(
            User.objects.all().order_by("created_date"),
            search.validated_data,
            allowed_eq=self.ALLOWED_EQ,
            allowed_contains=self.ALLOWED_CONTAINS,
            allowed_sort=self.ALLOWED_SORT,
        )
        return paginated_response(qs, search.validated_data, UserSerializer)


class UserDetailView(APIView):
    """PATCH/DELETE /api/users/<id>/  — admin actions"""
    permission_classes = [IsAuthenticated, IsAdmin]

    def _get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    def patch(self, request, user_id):
        user = self._get_user(user_id)
        if not user:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Prevent admin from deactivating themselves
        if "is_active" in request.data and str(user.id) == str(request.user.id):
            return Response(
                {"error": "Nu puteți dezactiva propriul cont de administrator."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AdminUserUpdateSerializer(
            user, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()

        return Response(UserSerializer(user).data)

    def delete(self, request, user_id):
        user = self._get_user(user_id)
        if not user:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Prevent admin from deleting themselves
        if str(user.id) == str(request.user.id):
            return Response(
                {"error": "Nu puteți șterge propriul cont de administrator."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Delete from Keycloak
        try:
            admin = get_keycloak_admin()
            admin.delete_user(str(user.id))
        except Exception:
            pass  # User may not exist in Keycloak

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminCreateUserView(APIView):
    """POST /api/users/create/  — admin creates a new user"""
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = AdminUserCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        full_name = serializer.validated_data["full_name"]
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        role = serializer.validated_data.get("role", "user")

        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else "-"

        admin = get_keycloak_admin()
        try:
            kc_user_id = admin.create_user(
                {
                    "email": email,
                    "username": email,
                    "firstName": first_name,
                    "lastName": last_name,
                    "enabled": True,
                    "emailVerified": True,
                    "requiredActions": [],
                    "credentials": [{
                        "type": "password",
                        "value": password,
                        "temporary": False,
                    }],
                },
                exist_ok=False,
            )
            admin.update_user(kc_user_id, {"requiredActions": []})
        except KeycloakPostError as e:
            if getattr(e, "response_code", None) == 409:
                return Response(
                    {"email": "Email already registered"},
                    status=status.HTTP_409_CONFLICT,
                )
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Assign realm role in Keycloak if admin
        if role == "admin":
            try:
                realm_roles = admin.get_realm_roles()
                admin_role = next(
                    (r for r in realm_roles if r["name"] == "admin"), None
                )
                if admin_role:
                    admin.assign_realm_roles(
                        user_id=kc_user_id,
                        roles=[admin_role],
                    )
            except Exception:
                pass  # Role assignment is best-effort

        try:
            user = User.objects.create(
                id=kc_user_id,
                email=email,
                full_name=full_name,
                role=role,
                is_active=True,
            )
        except Exception:
            admin.delete_user(kc_user_id)
            raise

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class AuthRegisterView(APIView):
    """POST /api/users/auth/register/"""
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.error, status=status.HTTP_400_BAD_REQUEST)
        
        full_name = serializer.validated_data["full_name"]
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else "-"

        admin = get_keycloak_admin()
        try:
            kc_user_id = admin.create_user(
                {
                    "email": email,
                    "username": email,
                    "firstName": first_name,
                    "lastName": last_name,
                    "enabled": True,
                    "emailVerified": True,
                    "requiredActions": [],
                    "credentials": [{
                        "type": "password",
                        "value": password,
                        "temporary": False,
                    }],
                },
                exist_ok=False,
            )
            admin.update_user(kc_user_id, {"requiredActions": []})
        except KeycloakPostError as e:
            if getattr(e,"response_code", None) == 409:
                return Response(
                    {"email": "Email already registered"},
                    status=status.HTTP_409_CONFLICT,
                )
            return Response(
                {"detail":str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            user = User.objects.create(
                id=kc_user_id,
                email=email,
                full_name=full_name,
                role="user",
                is_active=True,
            )
        except Exception:
            admin.delete_user(kc_user_id)
            raise

        kc = get_keycloak_openid()
        token = kc.token(username=email, password=password)

        return Response(
              {
                  "user": UserSerializer(user).data,
                  "access_token": token["access_token"],
                  "refresh_token": token["refresh_token"],
                  "expires_in": token["expires_in"],
                  "token_type": "Bearer",
              },
              status=status.HTTP_201_CREATED,
          )

class AuthLoginView(APIView):
      """POST /api/users/auth/login/"""
      authentication_classes = []
      permission_classes = [AllowAny]

      def post(self, request):
          serializer = LoginSerializer(data=request.data)
          if not serializer.is_valid():
              return Response(serializer.errors,
  status=status.HTTP_400_BAD_REQUEST)

          email = serializer.validated_data["email"]
          password = serializer.validated_data["password"]

          kc = get_keycloak_openid()
          try:
              token = kc.token(username=email, password=password)
          except KeycloakAuthenticationError:
              return Response(
                  {"detail": "Invalid credentials"},
                  status=status.HTTP_401_UNAUTHORIZED,
              )

          try:
              user = User.objects.get(email=email)
          except User.DoesNotExist:
              userinfo = kc.userinfo(token["access_token"])
              user = User.objects.create(
                  id=userinfo["sub"],
                  email=email,
                  full_name=userinfo.get("name", ""),
                  role="user",
                  is_active=True,
              )

          return Response({
              "user": UserSerializer(user).data,
              "access_token": token["access_token"],
              "refresh_token": token["refresh_token"],
              "expires_in": token["expires_in"],
              "token_type": "Bearer",
          })

class AuthRefreshView(APIView):
      """POST /api/users/auth/refresh/"""
      authentication_classes = []
      permission_classes = [AllowAny]

      def post(self, request):
          serializer = RefreshSerializer(data=request.data)
          if not serializer.is_valid():
              return Response(serializer.errors,
  status=status.HTTP_400_BAD_REQUEST)

          kc = get_keycloak_openid()
          try:
              token = kc.refresh_token(serializer.validated_data["refresh_token"])
          except Exception:
              return Response(
                  {"detail": "Invalid refresh token"},
                  status=status.HTTP_401_UNAUTHORIZED,
              )

          return Response({
              "access_token": token["access_token"],
              "refresh_token": token["refresh_token"],
              "expires_in": token["expires_in"],
          })
       
class UsersStatisticsView(APIView):
    """GET /api/users/statistics/"""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        from apps.predictions.models import Prediction
        from apps.training.models import TrainingData, RunHistory

        start_of_month = timezone.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        # Active model info
        active_model = RunHistory.objects.filter(is_active=True).first()

        stats = {
            "total_number": User.objects.count(),
            "number_of_admins": User.objects.filter(role="admin").count(),
            "number_of_active": User.objects.filter(is_active=True).count(),
            "new_users_this_month": User.objects.filter(
                created_date__gte=start_of_month
            ).count(),
            "total_predictions": Prediction.objects.count(),
            "new_predictions_this_month": Prediction.objects.filter(
                created_at__gte=start_of_month
            ).count(),
            "dataset_size": TrainingData.objects.count(),
            "model_accuracy": active_model.accuracy if active_model else None,
            "model_version": active_model.version if active_model else None,
            "last_trained_date": active_model.date if active_model else None,
        }
        return Response(TotalUsersSerializer(stats).data)

