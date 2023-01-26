import requests
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run demo requests for the example project API"

    def add_arguments(self, parser):
        parser.add_argument("--url", type=str, default="http://localhost:8000")

    def handle(self, *args, **options):
        base_url = options["url"]

        # Ninja Sync
        create_response = requests.post(
            f"{base_url}/ninja/sync/add-item",
            json={
                "created_by": "demo_user",
                "tags": ["demo_tag"],
                "heading": "Demo sync heading",
                "content": "Demo sync content",
            },
        )
        requests.get(f"{base_url}/ninja/sync/items")
        requests.delete(f"{base_url}/ninja/sync/item/{create_response.json()['id']}")

        # Ninja Async
        create_response = requests.post(
            f"{base_url}/ninja/async/add-item",
            json={
                "created_by": "demo_user",
                "tags": ["demo_tag"],
                "heading": "Demo async heading",
                "content": "Demo async content",
            },
        )
        requests.get(f"{base_url}/ninja/async/items")
        requests.delete(f"{base_url}/ninja/async/item/{create_response.json()['id']}")

        # Ninja query examples
        requests.get(f"{base_url}/ninja/query-examples/duplicate-query")
        requests.get(f"{base_url}/ninja/query-examples/similar-query")
        requests.get(f"{base_url}/ninja/query-examples/n-plus-1-query")

        # Ninja error examples
        requests.get(f"{base_url}/ninja/error-examples/divide-by-zero")
        requests.get(f"{base_url}/ninja/error-examples/not-authenticated")

        # Django REST Framework function based views
        create_response = requests.post(
            f"{base_url}/rest-framework/notes/",
            json={
                "created_by": "demo_user",
                "tags": ["demo_tag"],
                "heading": "Demo async heading",
                "content": "Demo async content",
            },
        )
        requests.get(f"{base_url}/rest-framework/notes/")
        requests.delete(
            f"{base_url}/rest-framework/notes/{create_response.json()['id']}"
        )

        # Django REST Framework class based views
        create_response = requests.post(
            f"{base_url}/rest-framework/class/notes/",
            json={
                "created_by": "demo_user",
                "tags": ["demo_tag"],
                "heading": "Demo async heading",
                "content": "Demo async content",
            },
        )
        requests.get(f"{base_url}/rest-framework/class/notes/")
        requests.delete(
            f"{base_url}/rest-framework/class/notes/{create_response.json()['id']}"
        )
