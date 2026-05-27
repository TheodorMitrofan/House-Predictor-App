import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Prediction
from .serializers import PredictionRequestSerializer, PredictionSerializer
from .ai_service import generate_explanation, generate_tips


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


class PredictionListView(APIView):
    """GET /api/predictions/history/  — [Profile] Vizualizare Istoric Predictii"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        predictions = Prediction.objects.filter(user=request.user)

        search    = request.query_params.get("search", "")
        prop_type = request.query_params.get("type", "")

        if search:
            predictions = (
                predictions.filter(location__icontains=search)
                | predictions.filter(property_type__icontains=search)
            )
        if prop_type and prop_type != "All":
            predictions = predictions.filter(property_type=prop_type)

        return Response(PredictionSerializer(predictions, many=True).data)


class PredictionDetailView(APIView):
    """GET /api/predictions/<id>/  — [Results] Vizualizare Rezultate"""
    permission_classes = [IsAuthenticated]

    def get(self, request, prediction_id):
        try:
            prediction = Prediction.objects.get(id=prediction_id, user=request.user)
        except Prediction.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(PredictionSerializer(prediction).data)


class AIExplainView(APIView):
    """POST /api/predictions/<id>/ai-explain/  — AI explanation for a prediction"""
    permission_classes = [IsAuthenticated]

    def post(self, request, prediction_id):
        try:
            prediction = Prediction.objects.get(id=prediction_id, user=request.user)
        except Prediction.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if prediction.ai_explanation:
            return Response({"explanation": prediction.ai_explanation})

        if not settings.OPENAI_API_KEY:
            return Response(
                {"error": "AI service not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            explanation = generate_explanation(prediction)
            prediction.ai_explanation = explanation
            prediction.save(update_fields=["ai_explanation"])
            return Response({"explanation": explanation})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class AITipsView(APIView):
    """POST /api/predictions/<id>/ai-tips/  — AI renovation tips"""
    permission_classes = [IsAuthenticated]

    def post(self, request, prediction_id):
        try:
            prediction = Prediction.objects.get(id=prediction_id, user=request.user)
        except Prediction.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if prediction.ai_tips_data:
            return Response(prediction.ai_tips_data)

        if not settings.OPENAI_API_KEY:
            return Response(
                {"error": "AI service not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            tips_data = generate_tips(prediction)
            prediction.ai_tips_data = tips_data
            prediction.save(update_fields=["ai_tips_data"])
            return Response(tips_data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
