from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView

from .views import CreateRequestView, HealthCheckView, MyRequestsView, RegisterView, RequestActionView

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health'),
    path('auth/register', RegisterView.as_view(), name='register'),
    path('auth/login', TokenObtainPairView.as_view(), name='login'),
    path('requests/', CreateRequestView.as_view(), name='request-create'),
    path('requests/my/', MyRequestsView.as_view(), name='request-my'),
    path('requests/<int:pk>/action/', RequestActionView.as_view(), name='request-action'),
]
