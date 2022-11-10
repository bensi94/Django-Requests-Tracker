from django.urls import path

from requests_tracker import APP_NAME, views

app_name = APP_NAME
urlpatterns = [
    path("", views.index, name="index"),
    path(
        "request-details/<uuid:request_id>",
        views.request_details,
        name="request_details",
    ),
]
