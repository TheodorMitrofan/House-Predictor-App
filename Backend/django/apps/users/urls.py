from django.urls import path
from .views import (
    MeView,
    UserSearchView,
    UserDetailView,
    AdminCreateUserView,
    AuthRegisterView,
    AuthLoginView,
    AuthRefreshView,
    UsersStatisticsView
)

urlpatterns = [
    path("me/",              MeView.as_view()),
    path("search/",          UserSearchView.as_view()),
    path("create/",          AdminCreateUserView.as_view()),
    path("<uuid:user_id>/",  UserDetailView.as_view()),
    path("auth/register/",   AuthRegisterView.as_view()),
    path("auth/login/",      AuthLoginView.as_view()),
    path("auth/refresh/",    AuthRefreshView.as_view()),
    path("statistics/",      UsersStatisticsView.as_view())
]
