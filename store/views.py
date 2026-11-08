from django.shortcuts import render
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend

from .models import Book
from .serializers import BookSerializer


def api_root(request):
    """Индексная страница API — http://127.0.0.1:8000/"""
    return render(request, "store/index.html")


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["price"]
