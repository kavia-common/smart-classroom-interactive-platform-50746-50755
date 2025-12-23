import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from api.models import UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = "Create an initial admin user from environment variables (non-interactive)."

    def handle(self, *args, **options):
        username = os.getenv("INITIAL_ADMIN_USERNAME")
        password = os.getenv("INITIAL_ADMIN_PASSWORD")
        email = os.getenv("INITIAL_ADMIN_EMAIL", "")

        if not username or not password:
            self.stdout.write(
                self.style.WARNING(
                    "INITIAL_ADMIN_USERNAME and INITIAL_ADMIN_PASSWORD are not set. "
                    "Skipping admin creation."
                )
            )
            return

        user, created = User.objects.get_or_create(username=username, defaults={"email": email})
        if created:
            user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        if email:
            user.email = email
        user.save()

        # Ensure profile exists and is ADMIN
        profile = getattr(user, "profile", None)
        if profile:
            profile.role = UserProfile.Role.ADMIN
            profile.save()

        self.stdout.write(self.style.SUCCESS(f"Initial admin ensured: {username}"))
