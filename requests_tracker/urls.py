from django.urls import path

from requests_tracker import APP_NAME, views

app_name = APP_NAME
urlpatterns = [
    path("", views.index, name="index"),
    path("delete", views.clear_request_list, name="delete_requests"),
    path("<uuid:request_id>", views.single_request_item, name="single_list_request"),
    path(
        "request-details/<uuid:request_id>",
        views.request_details,
        name="request_details",
    ),
    path("django-settings", views.django_settings, name="django_settings"),
]
