from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from restframework_app.models import NoteDRFApp as Note
from restframework_app.serializers import NoteSerializer


@api_view(["GET", "POST"])
def notes_function_view(request: Request) -> Response:
    if request.method == "GET":
        notes = (
            Note.objects.prefetch_related("tagdrfapp_set")
            .select_related("created_by")
            .all()
        )
        serializer = NoteSerializer(notes, many=True)
        return Response(serializer.data)
    elif request.method == "POST":
        serializer = NoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
def delete_note_function_view(request: Request, note_id: int) -> Response:
    note_to_delete = get_object_or_404(Note, id=note_id)
    note_to_delete.delete()

    return Response({"success": True}, status=status.HTTP_200_OK)


class NoteClassViewList(APIView):
    def get(self, request: Request) -> Response:
        notes = (
            Note.objects.prefetch_related("tagdrfapp_set")
            .select_related("created_by")
            .all()
        )
        serializer = NoteSerializer(notes, many=True)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = NoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class NoteClassViewDetail(APIView):
    def delete(self, request: Request, note_id: int) -> Response:
        note_to_delete = get_object_or_404(Note, id=note_id)
        note_to_delete.delete()

        return Response({"success": True}, status=status.HTTP_200_OK)
