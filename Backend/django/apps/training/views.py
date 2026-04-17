import csv
import io
import json
import requests

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

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


class RunHistoryListView(APIView):
    """GET /api/training/run-history/"""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        runs = RunHistory.objects.all()
        return Response(RunHistorySerializer(runs, many=True).data)


class ActiveModelView(APIView):
    """GET /api/training/active-model/  — stats card in admin Model Training page"""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        active = RunHistory.objects.filter(is_active=True).first()
        if not active:
            return Response({"error": "Niciun model activ."}, status=status.HTTP_404_NOT_FOUND)
        return Response(RunHistorySerializer(active).data)


# ── Data Management ───────────────────────────────────────────────────

class TrainingDataListView(APIView):
    """
    GET  /api/training/data/  — paginated table with optional search
    POST /api/training/data/  — Add Entry (single row)
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        search = request.query_params.get("search", "")
        entries = TrainingData.objects.all()
        if search:
            entries = entries.filter(zipcode__icontains=search)
        return Response(TrainingDataSerializer(entries[:200], many=True).data)

    def post(self, request):
        serializer = TrainingDataWriteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrainingDataDetailView(APIView):
    """DELETE /api/training/data/<id>/"""
    permission_classes = [IsAuthenticated, IsAdmin]

    def delete(self, request, entry_id):
        try:
            entry = TrainingData.objects.get(id=entry_id)
        except TrainingData.DoesNotExist:
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
