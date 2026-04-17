from django.urls import path
from .views import PredictionCreateView, PredictionListView, PredictionDetailView

urlpatterns = [
    path("",                          PredictionCreateView.as_view()),  # POST
    path("history/",                  PredictionListView.as_view()),    # GET
    path("<uuid:prediction_id>/",     PredictionDetailView.as_view()),  # GET
]
