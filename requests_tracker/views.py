from uuid import UUID

from django.template.response import TemplateResponse

from requests_tracker.middleware import RequestWithCollectors


def is_htmx_request(request: RequestWithCollectors) -> bool:
    return request.headers.get("HX-Request", "").lower() == "true"


def index(request: RequestWithCollectors) -> TemplateResponse:
    requests = {
        request_id: request_collector.get_as_context()
        for request_id, request_collector in reversed(
            request.request_collectors.items()
        )
    }

    return TemplateResponse(request, "index.html", context={"requests": requests})


def request_details(
    request: RequestWithCollectors, request_id: UUID
) -> TemplateResponse:
    template = (
        "partials/request_details_partial.html"
        if is_htmx_request(request)
        else "request_details.html",
    )
    context = request.request_collectors[request_id].get_as_context()

    return TemplateResponse(request=request, template=template, context=context)
