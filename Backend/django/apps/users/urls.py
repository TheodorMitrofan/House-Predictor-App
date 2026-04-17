from django.urls import path
from .views import MeView, UserListView, UserDetailView

urlpatterns = [
    path("me/",              MeView.as_view()),
    path("",                 UserListView.as_view()),
    path("<uuid:user_id>/",  UserDetailView.as_view()),
]
