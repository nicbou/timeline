from rest_framework import viewsets, permissions

from archive.models import JsonArchive, GpxArchive, N26CsvArchive, TelegramArchive
from archive.models.google_takeout import GoogleTakeoutArchive
from archive.models.twitter import TwitterArchive
from archive.serializers import GoogleTakeoutArchiveSerializer, TwitterArchiveSerializer, JsonArchiveSerializer, \
    GpxArchiveSerializer, N26CsvArchiveSerializer, TelegramArchiveSerializer


class GoogleTakeoutArchiveViewSet(viewsets.ModelViewSet):
    queryset = GoogleTakeoutArchive.objects.all()
    serializer_class = GoogleTakeoutArchiveSerializer
    permission_classes = [permissions.AllowAny]


class TwitterArchiveViewSet(viewsets.ModelViewSet):
    queryset = TwitterArchive.objects.all()
    serializer_class = TwitterArchiveSerializer
    permission_classes = [permissions.AllowAny]


class JsonArchiveViewSet(viewsets.ModelViewSet):
    queryset = JsonArchive.objects.all()
    serializer_class = JsonArchiveSerializer
    permission_classes = [permissions.AllowAny]


class GpxArchiveViewSet(viewsets.ModelViewSet):
    queryset = GpxArchive.objects.all()
    serializer_class = GpxArchiveSerializer
    permission_classes = [permissions.AllowAny]


class N26CsvArchiveViewSet(viewsets.ModelViewSet):
    queryset = N26CsvArchive.objects.all()
    serializer_class = N26CsvArchiveSerializer
    permission_classes = [permissions.AllowAny]


class TelegramArchiveViewSet(viewsets.ModelViewSet):
    queryset = TelegramArchive.objects.all()
    serializer_class = TelegramArchiveSerializer
    permission_classes = [permissions.AllowAny]
