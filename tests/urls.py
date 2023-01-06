from django.urls import include, path

from tests.fake_views import fake_view

urlpatterns = [
    path("__requests-tracker__/", include("requests_tracker.urls")),
    path("", view=fake_view),
]
