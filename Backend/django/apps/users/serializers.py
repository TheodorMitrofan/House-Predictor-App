from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "full_name", "email", "is_active", "role",
                  "location", "description", "created_date"]
        read_only_fields = ["id", "email", "created_date"]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["full_name", "location", "description"]


class AdminUserCreateSerializer(serializers.Serializer):
    """Used by admin to create a new user (Keycloak + local DB)."""
    full_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(min_length=6, write_only=True)
    role = serializers.ChoiceField(choices=["user", "admin"], default="user")


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """
    Admin can update full_name, role and is_active.
    Email is intentionally excluded — it cannot be changed.
    """
    class Meta:
        model = User
        fields = ["full_name", "role", "is_active"]


class RegisterSerializer(serializers.Serializer):
      full_name = serializers.CharField(required=True)
      email = serializers.EmailField(required=True)
      password = serializers.CharField(min_length=6, write_only=True)


class LoginSerializer(serializers.Serializer):
      email = serializers.EmailField(required=True)
      password = serializers.CharField(write_only=True)


class RefreshSerializer(serializers.Serializer):
      refresh_token = serializers.CharField(required=True)

class TotalUsersSerializer(serializers.Serializer):
      total_number = serializers.IntegerField()
      number_of_admins = serializers.IntegerField()
      number_of_active = serializers.IntegerField()
      new_users_this_month = serializers.IntegerField()
      total_predictions = serializers.IntegerField()
      new_predictions_this_month = serializers.IntegerField()
      dataset_size = serializers.IntegerField()
      model_accuracy = serializers.FloatField(allow_null=True)
      model_version = serializers.CharField(allow_null=True)
      last_trained_date = serializers.DateTimeField(allow_null=True)
