import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.common.search import SearchSerializer, apply_search, paginated_response
from .models import Prediction
from .serializers import PredictionRequestSerializer, PredictionSerializer


def call_ml_service(payload: dict) -> dict:
    try:
        response = requests.post(
            f"{settings.ML_SERVICE_URL}/predict",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        raise Exception("Modelul nostru de predicție întâmpină întârzieri. Încercați din nou.")
    except requests.RequestException as e:
        raise Exception(f"Eroare API Model ML: {e}")


class PredictionCreateView(APIView):
    """POST /api/predictions/  — [Input] Introducere date predictie"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PredictionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        payload = serializer.validated_data

        try:
            ml_result = call_ml_service(payload)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        prediction = Prediction.objects.create(
            user=request.user,
            prediction_value=ml_result["predicted_price"],
            confidence=ml_result["confidence"],
            explanation=ml_result.get("explanation", ""),
            price_factors=ml_result.get("price_factors", {}),
            tips=ml_result.get("tips", []),
            **payload,
        )

        return Response(PredictionSerializer(prediction).data, status=status.HTTP_201_CREATED)


class PredictionSearchView(APIView):
    """POST /api/predictions/search/  — current user's predictions, paginated"""
    permission_classes = [IsAuthenticated]

    ALLOWED_EQ = {
        "property_type", "bedrooms", "bathrooms",
        "has_parking", "has_pool", "has_balcony", "has_elevator",
    }
    ALLOWED_CONTAINS = {"location", "property_type"}
    ALLOWED_SORT = {"created_at", "prediction_value", "floor_area", "year_built"}

    def post(self, request):
        search = SearchSerializer(data=request.data)
        search.is_valid(raise_exception=True)
        qs = apply_search(
            Prediction.objects.filter(user=request.user),
            search.validated_data,
            allowed_eq=self.ALLOWED_EQ,
            allowed_contains=self.ALLOWED_CONTAINS,
            allowed_sort=self.ALLOWED_SORT,
        )
        return paginated_response(qs, search.validated_data, PredictionSerializer)


class PredictionDetailView(APIView):
    """GET /api/predictions/<id>/  — [Results] Vizualizare Rezultate"""
    permission_classes = [IsAuthenticated]

    def get(self, request, prediction_id):
        try:
            prediction = Prediction.objects.get(id=prediction_id, user=request.user)
        except Prediction.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(PredictionSerializer(prediction).data)
