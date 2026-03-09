from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .serializers import (
    CustomTokenObtainPairSerializer,
    ForgotPasswordSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    UserSerializer,
)


def get_tokens_for_user(user: User) -> dict:
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterSerializer,
        responses={201: UserSerializer},
        summary='Register a new user',
        auth=[],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return Response(
            {
                'user': UserSerializer(user).data,
                **tokens,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer

    @extend_schema(
        request=CustomTokenObtainPairSerializer,
        responses={
            200: OpenApiResponse(
                description='JWT access and refresh tokens returned on successful login'
            )
        },
        summary='Login with email and password',
        auth=[],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=ForgotPasswordSerializer,
        responses={
            200: OpenApiResponse(
                description=(
                    'Always returns success; if email exists, a reset link/token is generated'
                )
            )
        },
        summary='Request a password reset',
        auth=[],
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email__iexact=email)
            signer = TimestampSigner()
            token = signer.sign(user.pk)
            # TODO: send email with reset link containing token
            # e.g. f"{frontend_url}/reset-password?token={token}"
        except User.DoesNotExist:
            pass

        return Response(
            {'detail': 'If this email exists, a reset link was sent.'},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=ResetPasswordSerializer,
        responses={
            200: OpenApiResponse(description='Password reset successful'),
            400: OpenApiResponse(description='Invalid or expired token'),
        },
        summary='Reset password using a reset token',
        auth=[],
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        signer = TimestampSigner()
        try:
            user_id = signer.unsign(token, max_age=3600)  # 1 hour
            user = User.objects.get(pk=user_id)
            user.set_password(new_password)
            user.save()
            return Response(
                {'detail': 'Password reset successful.'},
                status=status.HTTP_200_OK,
            )
        except (BadSignature, SignatureExpired, User.DoesNotExist):
            return Response(
                {'detail': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'refresh': {
                        'type': 'string',
                        'description': 'Refresh token to blacklist',
                    },
                },
                'required': ['refresh'],
            }
        },
        responses={
            205: OpenApiResponse(description='Logged out successfully'),
            400: OpenApiResponse(description='Missing or invalid refresh token'),
        },
        summary='Logout and blacklist refresh token',
    )
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {'detail': 'Invalid token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {'detail': 'Logged out successfully.'},
            status=status.HTTP_205_RESET_CONTENT,
        )
