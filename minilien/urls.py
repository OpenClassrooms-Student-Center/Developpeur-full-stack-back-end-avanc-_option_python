from django.urls import include, path

urlpatterns = [
    path("", include("liens.urls")),
]
