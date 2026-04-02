# TO DO BE INIT Project
# de pus in structura cand face bianca init
# de sters comentarii dupa ce se pune in structura proiectului
# de completat tabela de training data dupa ce se decide datasetul
import uuid
from django.db import models

class Role(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=50)

    class Meta:
        db_table = 'role'

class Authority(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length = 255)

    class Meta:
        db_table = 'authority'

class Role_Authority(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        db_column='role_id',
        related_name='role_authorities'
    )
    authority = models.ForeignKey(
        Authority,
        on_delete=models.CASCADE,
        db_column='authority_id',
        related_name='role_authorities'
    )

    class Meta:
        db_table = 'role_authority'
        unique_together = ('role', 'authority')

class User(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    full_name = models.CharField(max_length=200, db_column='fullName')
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True, db_column='isActive')

    class Meta:
        db_table = 'user'


class Prediction(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    prediction_value = models.BigIntegerField(db_column='predictionValue')
    location = models.CharField(max_length=255)
    property_type = models.CharField(max_length=100, db_column='propertyType')
    floor_area = models.IntegerField(db_column='floorArea')
    bedrooms = models.IntegerField()
    year_built = models.IntegerField(db_column='yearBuilt')
    confidence = models.FloatField()
    explanation = models.TextField(blank=True, null=True)
    price_factors = models.JSONField(db_column='priceFactors', blank=True, null=True)
    tips = models.JSONField(blank=True, null=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='user_id',
        related_name='predictions'
    )

    class Meta:
        db_table = 'prediction'


class RunHistory(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    date = models.DateField()
    duration = models.DurationField()
    accuracy = models.FloatField()
    dataset_size = models.BigIntegerField(db_column='datasetSize')
    success = models.BooleanField()

    class Meta:
        db_table = 'run_history'