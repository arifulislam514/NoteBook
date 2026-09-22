from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema
from common.response import success_response, error_response
from .models import User
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    AuthResponseSerializer,
    MeResponseSerializer,
)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    @extend_schema(
        tags=['Authentication'],
        summary='Register new user',
        description='Register a new account with email and password. Returns user details and JWT access/refresh tokens.',
        request=RegisterSerializer,
        responses={201: AuthResponseSerializer},
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            errors = serializer.errors
            if 'email' in errors:
                return error_response(str(errors['email'][0]), status=400)
            if 'password' in errors:
                return error_response(str(errors['password'][0]), status=400)
            return error_response("Invalid data provided", status=400)

        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        data = {
            "user": {
                "id": str(user.id),
                "email": user.email,
            },
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        }
        return success_response(data, status=201)


class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    @extend_schema(
        tags=['Authentication'],
        summary='Login user',
        description='Authenticate with email and password to receive JWT access and refresh tokens.',
        request=LoginSerializer,
        responses={200: AuthResponseSerializer},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Invalid credentials", status=401)

        email = serializer.validated_data['email'].lower().strip()
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return error_response("Invalid credentials", status=401)

        if not user.check_password(password):
            return error_response("Invalid credentials", status=401)

        if not user.is_active:
            return error_response("Account is inactive", status=401)

        refresh = RefreshToken.for_user(user)
        data = {
            "user": {
                "id": str(user.id),
                "email": user.email,
            },
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        }
        return success_response(data, status=200)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Authentication'],
        summary='Current user info',
        description='Retrieve the ID and email of the currently authenticated user.',
        responses={200: MeResponseSerializer},
    )
    def get(self, request):
        user = request.user
        return success_response({
            "id": str(user.id),
            "email": user.email,
        })
