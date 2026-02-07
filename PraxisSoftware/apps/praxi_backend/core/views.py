"""Core app views.

Contains:
- health: Health check endpoint
- LoginView: JWT token obtain with user/role info
- RefreshView: JWT token refresh
- MeView: Current authenticated user info
"""

from django.http import JsonResponse
from praxi_backend.core.serializers import LoginSerializer, RefreshSerializer, UserMeSerializer
from praxi_backend.core.services import build_login_response, check_db_health, refresh_access_token
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes as perm_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


def health(request):
    """Health check endpoint - no authentication required."""
    result = check_db_health()
    if not result.ok:
        return JsonResponse({"status": "error", "detail": result.detail}, status=503)
    return JsonResponse({"status": "ok"})


class LoginView(APIView):
    """Obtain JWT access and refresh tokens.

    POST /api/auth/login/
    Body: {"username": "...", "password": "..."}
    Returns: {"user": {...}, "access": "...", "refresh": "..."}
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        return Response(build_login_response(user), status=status.HTTP_200_OK)


class RefreshView(APIView):
    """Refresh JWT access token.

    POST /api/auth/refresh/
    Body: {"refresh": "..."}
    Returns: {"access": "..."}
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data["refresh"]
        access = refresh_access_token(refresh_token)

        return Response(
            {
                "access": access,
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """Get current authenticated user info.

    GET /api/auth/me/
    Returns: {"id": ..., "username": "...", "email": "...", "role": {...}}
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@perm_classes([IsAuthenticated])
def me(request):
    """Legacy /auth/me/ endpoint - use MeView instead."""
    user = request.user
    role_payload = None
    if getattr(user, "role_id", None):
        role_payload = {
            "name": user.role.name,
            "label": user.role.label,
        }

    return Response(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": role_payload,
        }
    )

