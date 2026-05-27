import csv
import io
import json
import requests

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.common.search import SearchSerializer, apply_search, paginated_response
from hpa.permissions import IsAdmin
from .models import RunHistory, TrainingData
from .serializers import RunHistorySerializer, TrainingDataSerializer, TrainingDataWriteSerializer


# ── Model Training ────────────────────────────────────────────────────

class RetrainView(APIView):
    """POST /api/training/retrain/  — admin only, kicks off background retrain"""
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        try:
            response = requests.post(
                f"{settings.ML_SERVICE_URL}/retrain",
                timeout=5,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({"message": "Reantrenare pornită. Verificați Training History pentru progres."})


class RunHistorySearchView(APIView):
    """POST /api/training/run-history/search/  — paginated run history with filters/sorters"""
    permission_classes = [IsAuthenticated, IsAdmin]

    ALLOWED_EQ = {"is_active", "success", "version"}
    ALLOWED_CONTAINS = {"version"}
    ALLOWED_SORT = {"date", "accuracy", "dataset_size"}

    def post(self, request):
        search = SearchSerializer(data=request.data)
        search.is_valid(raise_exception=True)
        qs = apply_search(
            RunHistory.objects.all(),
            search.validated_data,
            allowed_eq=self.ALLOWED_EQ,
            allowed_contains=self.ALLOWED_CONTAINS,
            allowed_sort=self.ALLOWED_SORT,
        )
        return paginated_response(qs, search.validated_data, RunHistorySerializer)


class ActiveModelView(APIView):
    """GET /api/training/active-model/  — stats card in admin Model Training page"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active = RunHistory.objects.filter(is_active=True).first()
        if not active:
            return Response({"error": "Niciun model activ."}, status=status.HTTP_404_NOT_FOUND)
        return Response(RunHistorySerializer(active).data)


class TrainingStatusView(APIView):
    """GET /api/training/status/  — proxies the FastAPI in-memory training state.

    Authenticated (not admin-only) so non-admin users can see the global
    "predictions paused" banner during a retrain.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            response = requests.get(
                f"{settings.ML_SERVICE_URL}/training-status",
                timeout=5,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(response.json())


# ── Data Management ───────────────────────────────────────────────────

class TrainingDataCreateView(APIView):
    """POST /api/training/data/  — Add Entry (single row)"""
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = TrainingDataWriteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrainingDataSearchView(APIView):
    """POST /api/training/data/search/  — paginated dataset with filters/sorters"""
    permission_classes = [IsAuthenticated, IsAdmin]

    ALLOWED_EQ = {"zipcode", "bedrooms", "grade", "condition", "yr_built", "waterfront"}
    ALLOWED_CONTAINS = {"condition"}
    ALLOWED_SORT = {"id", "price", "yr_built", "grade", "bedrooms", "sqft_living", "zipcode"}

    def post(self, request):
        search = SearchSerializer(data=request.data)
        search.is_valid(raise_exception=True)
        qs = apply_search(
            TrainingData.objects.all().order_by("id"),
            search.validated_data,
            allowed_eq=self.ALLOWED_EQ,
            allowed_contains=self.ALLOWED_CONTAINS,
            allowed_sort=self.ALLOWED_SORT,
        )
        return paginated_response(qs, search.validated_data, TrainingDataSerializer)


class TrainingDataDetailView(APIView):
    """PATCH/DELETE /api/training/data/<id>/"""
    permission_classes = [IsAuthenticated, IsAdmin]

    def _get_entry(self, entry_id):
        try:
            return TrainingData.objects.get(id=entry_id)
        except TrainingData.DoesNotExist:
            return None

    def patch(self, request, entry_id):
        entry = self._get_entry(entry_id)
        if not entry:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = TrainingDataWriteSerializer(entry, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(TrainingDataSerializer(entry).data)

    def delete(self, request, entry_id):
        entry = self._get_entry(entry_id)
        if not entry:
            return Response(status=status.HTTP_404_NOT_FOUND)
        entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UploadDatasetView(APIView):
    """POST /api/training/data/upload/  — bulk CSV or JSON upload"""
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "Niciun fișier încărcat."}, status=status.HTTP_400_BAD_REQUEST)

        filename = file.name.lower()
        try:
            if filename.endswith(".csv"):
                rows = self._parse_csv(file)
            elif filename.endswith(".json"):
                rows = self._parse_json(file)
            else:
                return Response(
                    {"error": "Format invalid. Acceptăm doar .CSV sau .JSON."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            return Response(
                {"error": f"Eroare structură date: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TrainingDataWriteSerializer(data=rows, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"inserted": len(rows)}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _parse_csv(self, file):
        text = file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        return list(reader)

    def _parse_json(self, file):
        data = json.loads(file.read().decode("utf-8"))
        return data if isinstance(data, list) else [data]
