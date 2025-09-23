from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout, get_user_model
from .serializers import RegisterSerializer, LoginSerializer, ProfileSerializer
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


User = get_user_model()
token_generator = PasswordResetTokenGenerator()


@api_view(["GET"])
@permission_classes([AllowAny])  # anyone can hit this endpoint
def check_auth(request):
    """
    Return whether the current user is authenticated.
    """
    if request.user.is_authenticated:
        return Response({"is_authenticated": True, "username": request.user.username})
    return Response({"is_authenticated": False})


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and token_generator.check_token(user, token):
        if user.is_active:
            return render(request, "invalid_verification.html")
        user.is_active = True
        user.save()
        return render(request, "email_verified.html")
    else:
        return render(request, "invalid_verification.html")


def render_login(request):
    return render(request, "login.html")


def render_gamification(request):
    return render(request, "gamification.html")


def render_rewards(request):
    return render(request, "rewards.html")


def render_history(request):
    return render(request, "history.html")


def render_dashboard(request):
    return render(request, "dashboard.html")


def render_test(request):
    return render(request, "test.html")


def render_signup(request):
    return render(request, "signup.html")


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save(is_active=False)
        user.send_verify_email()


class LoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        print(email, password)
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)  # creates session cookie
            return Response({"message": "Login successful"})
        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logged out"})


class ProfileView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
