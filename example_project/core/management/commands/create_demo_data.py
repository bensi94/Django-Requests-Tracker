from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from ninja_app.models import NoteNinjaApp, TagNinjaApp
from restframework_app.models import NoteDRFApp, TagDRFApp


class Command(BaseCommand):
    help = "Create demo data for the example project app"

    def handle(self, *args, **options):
        user = User.objects.create_user(
            username="demo_user",
            email="test@example.com",
            password="demo_password",
        )

        notes = NoteDRFApp.objects.bulk_create(
            [
                NoteDRFApp(
                    created_by=user,
                    heading=f"Note heading {i}",
                    content=f"Note content {i}",
                )
                for i in range(50)
            ]
        )

        TagDRFApp.objects.bulk_create(
            [TagDRFApp(value="Demo tag", note=note) for note in notes]
        )

        notes = NoteNinjaApp.objects.bulk_create(
            [
                NoteNinjaApp(
                    created_by=user,
                    heading=f"Note heading {i}",
                    content=f"Note content {i}",
                )
                for i in range(50)
            ]
        )

        TagNinjaApp.objects.bulk_create(
            [TagNinjaApp(value="Demo tag", note=note) for note in notes]
        )
