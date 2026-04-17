from rest_framework import serializers
from .models import RunHistory, TrainingData


class RunHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RunHistory
        fields = [
            "id", "date", "duration", "accuracy",
            "dataset_size", "success", "is_active",
            "version", "model_path",
        ]
        read_only_fields = fields


class TrainingDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingData
        fields = [
            "id", "date", "price", "bedrooms", "bathrooms",
            "sqft_living", "sqft_lot", "floors", "waterfront",
            "view", "condition", "grade", "sqft_above",
            "sqft_basement", "yr_built", "yr_renovated",
            "zipcode", "lat", "long", "sqft_living15", "sqft_lot15",
        ]


class TrainingDataWriteSerializer(serializers.ModelSerializer):
    """Used for manual Add Entry in the admin Data Management page."""
    class Meta:
        model = TrainingData
        exclude = ["id"]
