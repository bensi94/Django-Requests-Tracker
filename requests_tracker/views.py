from uuid import UUID

from django.template.response import TemplateResponse

from requests_tracker.middleware import RequestWithCollectors


def is_htmx_request(request: RequestWithCollectors) -> bool:
    return request.headers.get("HX-Request", "").lower() == "true"


def is_htmx_search_query(request: RequestWithCollectors) -> bool:
    return request.headers.get("HX-Target") == "request-list-search-results"


def index(request: RequestWithCollectors) -> TemplateResponse:
    search_filter = request.GET.get("requests_filter", "")

    requests = {
        request_id: request_collector.get_as_context()
        for request_id, request_collector in reversed(
            list(request.request_collectors.items())
        )
        if not search_filter or request_collector.matches_search_filter(search_filter)
    }

    template = "index.html"

    if is_htmx_search_query(request):
        template = "partials/request_list_only_partial.html"
    elif is_htmx_request(request):
        template = "partials/request_list_partial.html"

    return TemplateResponse(
        request,
        template,
        context={"requests": requests, "current_search": search_filter},
    )


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
