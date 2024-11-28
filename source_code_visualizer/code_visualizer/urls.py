from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_code, name='upload_code'),
    path('visualize/', views.upload_code, name='visualize_code'),
]
