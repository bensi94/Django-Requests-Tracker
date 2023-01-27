"""example_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from ninja_app.views import api as ninja_api
from rest_framework.schemas import get_schema_view
from restframework_app.views import (
    NoteClassViewDetail,
    NoteClassViewList,
    delete_note_function_view,
    notes_function_view,
)

urlpatterns = [
    path("ninja/", ninja_api.urls),
    path(
        "restframework/docs",
        get_schema_view(
            title="Example Project",
            description="Restframework App",
            version="1.0.0",
        ),
        name="openapi-schema",
    ),
    path("rest-framework/notes/", notes_function_view),
    path("rest-framework/notes/<int:note_id>/", delete_note_function_view),
    path("rest-framework/class/notes/", NoteClassViewList.as_view()),
    path("rest-framework/class/notes/<int:note_id>", NoteClassViewDetail.as_view()),
]
if settings.DEBUG:
    urlpatterns += [path("__requests_tracker__/", include("requests_tracker.urls"))]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
