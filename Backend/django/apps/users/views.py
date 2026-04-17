from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import User
from .serializers import UserSerializer, UserUpdateSerializer
from hpa.permissions import IsAdmin


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


class UserListView(APIView):
    """GET /api/users/  — admin: list + search users"""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        search = request.query_params.get("search", "")
        users = User.objects.all()
        if search:
            users = (
                users.filter(email__icontains=search)
                | users.filter(full_name__icontains=search)
            )
        return Response(UserSerializer(users, many=True).data)


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

        if "is_active" in request.data:
            user.is_active = request.data["is_active"]
            user.save()

        return Response(UserSerializer(user).data)

    def delete(self, request, user_id):
        user = self._get_user(user_id)
        if not user:
            return Response(status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
