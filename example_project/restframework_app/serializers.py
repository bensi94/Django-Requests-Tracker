from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from restframework_app.models import NoteDRFApp as Note
from restframework_app.models import TagDRFApp as Tag


class NoteSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    created_by = serializers.CharField(max_length=150)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=512),
        write_only=True,
    )
    heading = serializers.CharField(max_length=512)
    content = serializers.CharField()

    def create(self, validated_data):
        created_by_user = get_object_or_404(User, username=validated_data["created_by"])
        note = Note.objects.create(
            created_by=created_by_user,
            heading=validated_data["heading"],
            content=validated_data["content"],
        )
        Tag.objects.bulk_create(
            Tag(value=tag, note=note) for tag in validated_data["tags"]
        )
        return note

    def update(self, instance, validated_data):
        pass

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["tags"] = [tag.value for tag in instance.tagdrfapp_set.all()]
        return ret
