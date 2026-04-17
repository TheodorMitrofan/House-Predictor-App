from django.urls import path, include

urlpatterns = [
    path("api/users/",       include("apps.users.urls")),
    path("api/predictions/", include("apps.predictions.urls")),
    path("api/training/",    include("apps.training.urls")),
]
