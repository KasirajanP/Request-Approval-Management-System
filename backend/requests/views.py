from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Request
from .serializers import (
    ActionSerializer,
    RegisterSerializer,
    RequestCreateSerializer,
    RequestListSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)


class CreateRequestView(generics.CreateAPIView):
    serializer_class = RequestCreateSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if user.role != User.ROLE_EMPLOYEE:
            raise PermissionDenied('Only EMPLOYEE can create requests.')

        approver = serializer.validated_data.get('assigned_approver')
        if approver.role != User.ROLE_APPROVER:
            raise ValidationError({'assigned_approver': 'Assigned approver must have role APPROVER.'})

        serializer.save(created_by=user)


class MyRequestsView(generics.ListAPIView):
    serializer_class = RequestListSerializer

    def get_queryset(self):
        return Request.objects.filter(created_by=self.request.user).order_by('-created_at')


class RequestActionView(APIView):
    def post(self, request, pk: int):
        user = request.user
        if user.role != User.ROLE_APPROVER:
            raise PermissionDenied('Only APPROVER can approve or reject requests.')

        request_obj = get_object_or_404(Request, pk=pk)
        if request_obj.assigned_approver_id != user.id:
            raise PermissionDenied('Only the assigned approver can act on this request.')

        if request_obj.status != Request.STATUS_PENDING:
            raise ValidationError({'status': 'Request has already been acted on.'})

        serializer = ActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        request_obj.status = (
            Request.STATUS_APPROVED if action == 'APPROVE' else Request.STATUS_REJECTED
        )
        request_obj.save(update_fields=['status', 'updated_at'])

        return Response(
            {'id': request_obj.id, 'status': request_obj.status},
            status=status.HTTP_200_OK,
        )
