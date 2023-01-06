from typing import Type

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Router, Schema
from ninja_app.models import NoteNinjaApp as Note
from ninja_app.models import TagNinjaApp as Tag

api = NinjaAPI()
sync_router = Router()
async_router = Router()
query_examples = Router()
error_examples_router = Router()

api.add_router("/sync", sync_router, tags=["Sync"])
api.add_router("/async", async_router, tags=["Async"])
api.add_router("/query-examples", query_examples, tags=["Query Examples"])
api.add_router("/error-examples", error_examples_router, tags=["Error examples"])


class NoteIn(Schema):
    created_by: str
    tags: list[str]
    heading: str
    content: str


class NoteOut(NoteIn):
    id: int

    @classmethod
    def from_model(cls: Type["NoteOut"], obj: Note) -> "NoteOut":
        return NoteOut(
            id=obj.id,
            created_by=obj.created_by.username,
            tags=[tag.value for tag in obj.tagninjaapp_set.all()],
            heading=obj.heading,
            content=obj.content,
        )

    @classmethod
    async def afrom_model(cls: Type["NoteOut"], obj: Note) -> "NoteOut":
        return NoteOut(
            id=obj.id,
            created_by=obj.created_by.username,
            tags=[tag.value async for tag in obj.tagninjaapp_set.all()],
            heading=obj.heading,
            content=obj.content,
        )


class SuccessfulDelete(Schema):
    success: bool


@sync_router.post("/add-item", response=NoteOut)
def add(request: HttpRequest, payload: NoteIn) -> NoteOut:
    created_by_user = get_object_or_404(User, username=payload.created_by)
    note = Note.objects.create(
        created_by=created_by_user,
        heading=payload.heading,
        content=payload.content,
    )
    Tag.objects.bulk_create([Tag(value=tag, note=note) for tag in payload.tags])
    return NoteOut.from_model(note)


@sync_router.get("/items", response=list[NoteOut])
def get_notes(request: HttpRequest) -> list[NoteOut]:
    return [
        NoteOut.from_model(note)
        for note in Note.objects.select_related("created_by").all()
    ]


@sync_router.delete("/item/{item_id}", response=SuccessfulDelete)
def delete_note(request: HttpRequest, item_id: int) -> SuccessfulDelete:
    note_to_delete = get_object_or_404(Note, id=item_id)
    note_to_delete.delete()
    return SuccessfulDelete(success=True)


@async_router.post("/add-item", response=NoteOut)
async def async_add(request: HttpRequest, payload: NoteIn) -> NoteOut:
    try:
        created_by_user = await User.objects.aget(username=payload.created_by)
    except User.DoesNotExist as does_not_exist:
        raise Http404(
            f"No {User._meta.object_name} matches the given query."
        ) from does_not_exist

    note = await sync_to_async(Note.objects.create)(
        created_by=created_by_user,
        heading=payload.heading,
        content=payload.content,
    )
    await sync_to_async(Tag.objects.bulk_create)(
        [Tag(value=tag, note=note) for tag in payload.tags]
    )
    return await NoteOut.afrom_model(note)


@async_router.get("/items", response=list[NoteOut])
async def async_get_notes(request: HttpRequest) -> list[NoteOut]:
    return [
        await NoteOut.afrom_model(note)
        async for note in Note.objects.select_related("created_by").all()
    ]


@async_router.delete("/item/{item_id}", response=SuccessfulDelete)
async def async_delete_note(request: HttpRequest, item_id: int) -> SuccessfulDelete:
    try:
        note_to_delete = await Note.objects.aget(id=item_id)
    except Note.DoesNotExist as does_not_exist:
        raise Http404(
            f"No {Note._meta.object_name} matches the given query."
        ) from does_not_exist
    await sync_to_async(note_to_delete.delete)()
    return SuccessfulDelete(success=True)


@query_examples.get("/duplicate-query", response={204: None})
def duplicate_query(request: HttpRequest) -> None:
    """Execute the same query twice."""
    Note.objects.all().first()
    Note.objects.all().first()
    return 204, None


@query_examples.get("/similar-query", response={204: None})
def similar_query(request: HttpRequest) -> None:
    """Execute two similar queries."""
    Note.objects.filter(id=1).first()
    Note.objects.filter(id=2).first()
    return 204, None


@query_examples.get("/n-plus-1-query", response={204: None})
def n_plus_1_query(request: HttpRequest) -> None:
    """Execute a query that triggers the N+1 problem."""

    for note in Note.objects.all():
        print(note.created_by.username)
    return 204, None


@error_examples_router.get("/divide-by-zero", response=None)
def divide_by_zero(request: HttpRequest) -> None:
    10 / 0


@error_examples_router.get("/not-authenticated", auth=lambda _: False)
def not_authenticated(request: HttpRequest) -> None:
    pass
