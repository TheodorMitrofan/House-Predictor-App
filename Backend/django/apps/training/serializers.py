from rest_framework import serializers
from .models import RunHistory, TrainingData


class RunHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RunHistory
        fields = [
            "id", "date", "duration", "accuracy", "rmse",
            "dataset_size", "success", "is_active",
            "version", "model_path", "error_message",
        ]
        read_only_fields = fields


class TrainingDataSerializer(serializers.ModelSerializer):
    waterfront = serializers.SerializerMethodField()

    def get_waterfront(self, obj):
        return obj.waterfront == 'Y'

    class Meta:
        model = TrainingData
        fields = [
            "id", "date", "price", "bedrooms", "bathrooms",
            "sqft_living", "sqft_lot", "floors", "waterfront",
            "view", "condition", "grade", "sqft_above",
            "sqft_basement", "yr_built", "yr_renovated",
            "zipcode", "lat", "long", "sqft_living15", "sqft_lot15",
        ]


class WaterfrontField(serializers.Field):
    """Accepts bool (true/false) or string ('Y'/'N'/'0'/'1') → stores 'Y'/'N'."""
    def to_internal_value(self, data):
        if isinstance(data, bool):
            return 'Y' if data else 'N'
        if isinstance(data, str):
            if data.upper() in ('Y', 'YES', '1', 'TRUE'):
                return 'Y'
            if data.upper() in ('N', 'NO', '0', 'FALSE', ''):
                return 'N'
        raise serializers.ValidationError("Expected true/false or 'Y'/'N'.")

    def to_representation(self, value):
        return value == 'Y'


class TrainingDataWriteSerializer(serializers.ModelSerializer):
    """Used for manual Add Entry in the admin Data Management page."""
    waterfront = WaterfrontField(required=False, default='N')

    class Meta:
        model = TrainingData
        exclude = ["id"]
