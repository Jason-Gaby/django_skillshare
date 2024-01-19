from django.urls import path
from . import views

app_name = "profiles"

urlpatterns = [
    path("<str:username>/", views.ProfileDetailView.as_view(), name="detail"),
    path("<str:username>/edit/", views.ProfileDetailEdit.as_view(), name="edit"),
    path("<str:username>/follow/", views.FollowView.as_view(), name="follow"),
]
