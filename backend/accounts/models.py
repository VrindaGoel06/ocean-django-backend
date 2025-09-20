from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse

token_generator = PasswordResetTokenGenerator()


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, email, phone_number, password=None, **extra_fields):
        """
        Create and save a user with username, email, phone_number, and password.
        """
        if not username:
            raise ValueError("The Username field is required")
        if not email:
            raise ValueError("The Email field is required")
        if not phone_number:
            raise ValueError("The Phone number field is required")
        phone_number = str(phone_number).replace(" ", "")
        if not str(phone_number).startswith("+"):
            phone_number = "+91" + phone_number
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", extra_fields.get("is_staff", False))
        user = self.model(
            username=username, email=email, phone_number=phone_number, **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, username, email, phone_number, password=None, **extra_fields
    ):
        """
        Create and save a superuser with the given username, email, phone_number, and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, email, phone_number, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(blank=False, unique=True, null=False)
    phone_number = models.CharField(max_length=15, null=False, blank=False, unique=True)
    pincode = models.CharField(max_length=10, blank=False, null=True)

    objects = UserManager()  # ✅ attach custom manager

    REQUIRED_FIELDS = ["username", "phone_number"]
    USERNAME_FIELD = "email"

    def __str__(self):
        return f"{self.username} ({self.email})"

    def send_verify_email(self):
        uid = urlsafe_base64_encode(force_bytes(self.pk))
        token = token_generator.make_token(self)

        html_content = render_to_string(
            "email/verify_email.html",
            context={
                "domain": settings.DOMAIN,
                "verify_email_path": reverse(
                    "verify-email", kwargs={"uidb64": uid, "token": token}
                ),
            },
        )
        msg = EmailMessage(
            "Verify your email", html_content, settings.EMAIL_HOST_USER, [self.email]
        )
        msg.send()
