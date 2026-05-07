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
        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = max(int(request.query_params.get("page_size", 20)), 1)
        except (TypeError, ValueError):
            page_size = 20

        qs = TrainingData.objects.all().order_by("id")
        if search:
            qs = qs.filter(zipcode__icontains=search)

        total = qs.count()
        total_pages = (total + page_size - 1) // page_size if total else 1
        start = (page - 1) * page_size
        end = start + page_size

        return Response({
            "count": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "results": TrainingDataSerializer(qs[start:end], many=True).data,
        })

    def post(self, request):
        serializer = TrainingDataWriteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
