from django.urls import path
from .views import PredictionCreateView, PredictionListView, PredictionDetailView, AIExplainView, AITipsView

urlpatterns = [
    path("",                                       PredictionCreateView.as_view()),  # POST
    path("history/",                               PredictionListView.as_view()),    # GET
    path("<uuid:prediction_id>/",                  PredictionDetailView.as_view()),  # GET
    path("<uuid:prediction_id>/ai-explain/",       AIExplainView.as_view()),         # POST
    path("<uuid:prediction_id>/ai-tips/",          AITipsView.as_view()),            # POST
]
