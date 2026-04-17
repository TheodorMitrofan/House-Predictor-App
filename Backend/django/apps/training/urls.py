from django.urls import path
from .views import (
    RetrainView,
    RunHistoryListView,
    ActiveModelView,
    TrainingDataListView,
    TrainingDataDetailView,
    UploadDatasetView,
)

urlpatterns = [
    path("retrain/",             RetrainView.as_view()),
    path("run-history/",         RunHistoryListView.as_view()),
    path("active-model/",        ActiveModelView.as_view()),
    path("data/",                TrainingDataListView.as_view()),
    path("data/upload/",         UploadDatasetView.as_view()),
    path("data/<int:entry_id>/", TrainingDataDetailView.as_view()),
]
