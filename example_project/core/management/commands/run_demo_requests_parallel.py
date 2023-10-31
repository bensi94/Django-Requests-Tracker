import asyncio

import httpx
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run demo requests for the example project API in parallel asyncio loop"

    def add_arguments(self, parser):
        parser.add_argument("--url", type=str, default="http://localhost:8000")

    async def async_handle(self, base_url: str) -> None:
        responses: dict[str, dict] = {}

        async def send_get_request(client: httpx.AsyncClient, url: str) -> None:
            await client.get(url)

        async def send_post_request(
            client: httpx.AsyncClient, url: str, json: dict
        ) -> None:
            response = await client.post(url, json=json)
            responses[url] = response.json()

        async with httpx.AsyncClient() as request_client:
            # Ninja Sync
            await asyncio.gather(
                send_post_request(
                    request_client,
                    f"{base_url}/ninja/sync/add-item",
                    json={
                        "created_by": "demo_user",
                        "tags": ["demo_tag"],
                        "heading": "Demo sync heading",
                        "content": "Demo sync content",
                    },
                ),
                send_get_request(request_client, f"{base_url}/ninja/sync/items"),
            )
            await request_client.delete(
                f"{base_url}/ninja/sync/item/"
                f"{responses[f'{base_url}/ninja/sync/add-item']['id']}"
            )

            # Ninja Async
            await asyncio.gather(
                send_post_request(
                    request_client,
                    f"{base_url}/ninja/async/add-item",
                    json={
                        "created_by": "demo_user",
                        "tags": ["demo_tag"],
                        "heading": "Demo async heading",
                        "content": "Demo async content",
                    },
                ),
                send_get_request(request_client, f"{base_url}/ninja/async/items"),
            )
            await request_client.delete(
                f"{base_url}/ninja/async/item/"
                f"{responses[f'{base_url}/ninja/async/add-item']['id']}"
            )

            # Ninja query examples and error examples
            await asyncio.gather(
                *[
                    send_get_request(request_client, url)
                    for url in [
                        f"{base_url}/ninja/query-examples/duplicate-query",
                        f"{base_url}/ninja/query-examples/similar-query",
                        f"{base_url}/ninja/query-examples/n-plus-1-query",
                        f"{base_url}/ninja/error-examples/divide-by-zero",
                        f"{base_url}/ninja/error-examples/not-authenticated",
                    ]
                ]
            )

            # Django REST Framework function based views
            await asyncio.gather(
                send_post_request(
                    request_client,
                    f"{base_url}/rest-framework/notes/",
                    json={
                        "created_by": "demo_user",
                        "tags": ["demo_tag"],
                        "heading": "Demo async heading",
                        "content": "Demo async content",
                    },
                ),
                send_get_request(request_client, f"{base_url}/rest-framework/notes/"),
            )
            await request_client.delete(
                f"{base_url}/rest-framework/notes/"
                f"{responses[f'{base_url}/rest-framework/notes/']['id']}"
            )

            # Django REST Framework class based views
            await asyncio.gather(
                send_post_request(
                    request_client,
                    f"{base_url}/rest-framework/class/notes/",
                    json={
                        "created_by": "demo_user",
                        "tags": ["demo_tag"],
                        "heading": "Demo async heading",
                        "content": "Demo async content",
                    },
                ),
                send_get_request(
                    request_client, f"{base_url}/rest-framework/class/notes/"
                ),
            )
            await request_client.delete(
                f"{base_url}/rest-framework/class/notes/"
                f"{responses[f'{base_url}/rest-framework/class/notes/']['id']}"
            )

    def handle(self, *args, **options):
        base_url = options["url"]

        asyncio.run(self.async_handle(base_url))
