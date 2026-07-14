from django.contrib.auth import get_user_model, login
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.authentication import APIKeyAuthentication
from account.filters import UserFilter
from account.permissions import HasValidAPIKey
from account.serializers import (
    APIKeySerializer,
    UserListSerializer,
    UserLoginSerializer,
    UserRegisterSerializer,
)
from account.services import api_key_service
from account.tokens import UserRefreshToken
from ydm.utils.pagination import CustomPagination

User = get_user_model()


class UserRegisterAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = UserRefreshToken.for_user(user)
            return Response(
                {
                    "message": "User registered successfully.",
                    "username": user.username,
                    "first_name": user.first_name,
                    "email": user.email,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            login(request, user)  # Establish session login

            refresh = UserRefreshToken.for_user(user)

            return Response(
                {
                    "message": "Login successful.",
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class APIKeyListGenerateAPI(APIView):
    """
    GET: List all active API keys for the authenticated user.
    POST: Generate a new API key for the authenticated user (deactivates old ones).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        api_keys = user.api_keys.filter(is_active=True)
        serializer = APIKeySerializer(api_keys, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user

        # Deactivate old keys to ensure only one is active at a time
        user.api_keys.filter(is_active=True).update(is_active=False)

        # Generate new key
        api_key, raw_key = api_key_service.create_api_key(user=user)

        return Response(
            {
                "message": "New API Key generated successfully.",
                "api_key": raw_key,
                "created_at": api_key.created_at,
            },
            status=status.HTTP_201_CREATED,
        )


class UserListAPI(generics.ListAPIView):
    """
    GET: List all users in the system with pagination and filtering.
    """

    queryset = User.objects.all().order_by("first_name", "last_name")
    serializer_class = UserListSerializer
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = [HasValidAPIKey]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter
