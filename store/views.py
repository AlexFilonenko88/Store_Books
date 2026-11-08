from django.shortcuts import render
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.db.models import Max

from .models import Book
from .serializers import BookSerializer


def api_root(request):
    """Индексная страница API — http://127.0.0.1:8000/"""
    return render(request, "store/index.html")


class BookViewSet(viewsets.ModelViewSet):
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["price", "authors"]
    ordering_fields = ["price", "author_name"]
    ordering = ["price"]

    def get_queryset(self):
        return Book.objects.all().annotate(author_name=Max('authors__name'))
