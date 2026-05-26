from django.urls import path
from .views import (
    RetrainView,
    RunHistorySearchView,
    ActiveModelView,
    TrainingDataCreateView,
    TrainingDataSearchView,
    TrainingDataDetailView,
    UploadDatasetView,
)

urlpatterns = [
    path("retrain/",             RetrainView.as_view()),
    path("run-history/search/",  RunHistorySearchView.as_view()),
    path("active-model/",        ActiveModelView.as_view()),
    path("data/",                TrainingDataCreateView.as_view()),
    path("data/search/",         TrainingDataSearchView.as_view()),
    path("data/upload/",         UploadDatasetView.as_view()),
    path("data/<int:entry_id>/", TrainingDataDetailView.as_view()),
]
