import uuid
from django.db import models
from apps.users.models import User


class Prediction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prediction_value = models.BigIntegerField(db_column="predictionValue")
    location = models.CharField(max_length=255)
    property_type = models.CharField(max_length=100, db_column="propertyType")
    floor_area = models.IntegerField(db_column="floorArea")
    bedrooms = models.IntegerField()
    bathrooms = models.IntegerField(default=0)
    floor_number = models.IntegerField(default=0, db_column="floorNumber")
    year_built = models.IntegerField(db_column="yearBuilt")
    confidence = models.FloatField()
    explanation = models.TextField(blank=True, null=True)
    price_factors = models.JSONField(db_column="priceFactors", blank=True, null=True)
    tips = models.JSONField(blank=True, null=True)

    # Feature toggles (pills in the UI)
    has_parking = models.BooleanField(default=False, db_column="hasParking")
    has_pool = models.BooleanField(default=False, db_column="hasPool")
    has_balcony = models.BooleanField(default=False, db_column="hasBalcony")
    has_elevator = models.BooleanField(default=False, db_column="hasElevator")

    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        db_column="user_id", related_name="predictions"
    )

    class Meta:
        db_table = "prediction"
        ordering = ["-created_at"]
