"""Core app views.

Contains:
- health: Health check endpoint
- LoginView: JWT token obtain with user/role info
- RefreshView: JWT token refresh
- MeView: Current authenticated user info
- setup_database: Temporary setup endpoint for Vercel deployment
"""

import os
from io import StringIO

from django.core.management import call_command
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
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


# ============================================================
# Temporary Setup Endpoint for Vercel Deployment
# ⚠️ DELETE THIS AFTER FIRST USE!
# ============================================================


@require_http_methods(["GET"])
def setup_database(request):
    """
    Temporary endpoint to run migrations and create admin user.
    Only works with the correct secret key.
    
    Usage: GET /setup/?secret=YOUR_SECRET
    
    ⚠️ DELETE THIS VIEW AFTER FIRST USE!
    """
    # Check secret key
    secret = request.GET.get('secret')
    expected_secret = os.environ.get('SETUP_SECRET', 'setup-praxiapp-2026')
    
    if secret != expected_secret:
        return JsonResponse({
            'error': 'Unauthorized',
            'message': 'Invalid secret key'
        }, status=403)
    
    try:
        # Capture command output
        out = StringIO()
        
        # Run the setup command
        call_command('setup_production', stdout=out)
        
        output = out.getvalue()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Database setup completed',
            'output': output,
            'credentials': {
                'username': 'admin',
                'password': 'praxiapp2026!Admin',
                'note': 'CHANGE THIS PASSWORD IMMEDIATELY AFTER LOGIN!'
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

