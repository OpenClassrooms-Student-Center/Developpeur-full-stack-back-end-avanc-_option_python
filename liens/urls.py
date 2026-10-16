from django.urls import path

from . import views

urlpatterns = [
    path("api/liens", views.liens),
    path("api/liens/<str:code>", views.lien),
    path("r/<str:code>", views.rediriger),
]
