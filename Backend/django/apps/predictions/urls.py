from django.urls import path
from .views import PredictionCreateView, PredictionSearchView, PredictionDetailView, AIExplainView, AITipsView

urlpatterns = [
    path("",                                   PredictionCreateView.as_view()),  # POST create
    path("search/",                            PredictionSearchView.as_view()),  # POST search
    path("<uuid:prediction_id>/",              PredictionDetailView.as_view()),  # GET detail
    path("<uuid:prediction_id>/ai-explain/",   AIExplainView.as_view()),         # POST
    path("<uuid:prediction_id>/ai-tips/",      AITipsView.as_view()),            # POST
]
