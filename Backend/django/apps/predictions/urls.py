from django.urls import path
from .views import PredictionCreateView, PredictionSearchView, PredictionDetailView

urlpatterns = [
    path("",                          PredictionCreateView.as_view()),  # POST create
    path("search/",                   PredictionSearchView.as_view()),  # POST search
    path("<uuid:prediction_id>/",     PredictionDetailView.as_view()),  # GET detail
]
