from django.http import HttpResponse

from requests_tracker.middleware import RequestWithCollectors


def fake_view(request: RequestWithCollectors) -> HttpResponse:
    return HttpResponse(f"Fake response of: {request.path}")
