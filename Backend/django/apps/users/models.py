import uuid
from django.db import models


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=50)

    class Meta:
        db_table = "role"


class Authority(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255)

    class Meta:
        db_table = "authority"


class RoleAuthority(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE,
        db_column="role_id", related_name="role_authorities"
    )
    authority = models.ForeignKey(
        Authority, on_delete=models.CASCADE,
        db_column="authority_id", related_name="role_authorities"
    )

    class Meta:
        db_table = "role_authority"
        unique_together = ("role", "authority")


class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=200, db_column="fullName")
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True, db_column="isActive")
    location = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    role = models.TextField(max_length=50)
    created_date = models.DateTimeField(auto_now_add=True, db_column="createdDate")

    class Meta:
        db_table = "user"

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def __str__(self):
        return self.email
