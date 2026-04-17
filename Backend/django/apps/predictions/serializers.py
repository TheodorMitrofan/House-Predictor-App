from rest_framework import serializers
from .models import Prediction


class PredictionRequestSerializer(serializers.Serializer):
    """Validates the [Input] Introducere date predictie form."""
    location      = serializers.CharField(min_length=2)
    property_type = serializers.ChoiceField(choices=["Apartment", "House", "Villa"])
    floor_area    = serializers.FloatField(min_value=1)
    bedrooms      = serializers.IntegerField(min_value=0)
    bathrooms     = serializers.IntegerField(min_value=0, default=0)
    year_built    = serializers.IntegerField(min_value=1800, max_value=2026)
    floor_number  = serializers.IntegerField(default=0)
    has_parking   = serializers.BooleanField(default=False)
    has_pool      = serializers.BooleanField(default=False)
    has_balcony   = serializers.BooleanField(default=False)
    has_elevator  = serializers.BooleanField(default=False)


class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = [
            "id", "prediction_value", "location", "property_type",
            "floor_area", "bedrooms", "bathrooms", "floor_number",
            "year_built", "confidence", "explanation", "price_factors",
            "tips", "has_parking", "has_pool", "has_balcony",
            "has_elevator", "created_at",
        ]
        read_only_fields = fields
