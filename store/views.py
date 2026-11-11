from django.db.models import Avg, Count, Max
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Book, BookLike, BookRating
from .serializers import BookRatingSerializer, BookSerializer


def api_root(request):
    """Индексная страница API — http://127.0.0.1:8000/"""
    return render(request, "store/index.html")


class BookViewSet(viewsets.ModelViewSet):
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["price", "authors"]
    ordering_fields = ["price", "author_name", "likes_count", "rating_avg"]
    ordering = ["price"]

    def get_queryset(self):
        return (
            Book.objects.all()
            .annotate(
                author_name=Max("authors__name"),
                likes_count=Count("likes", distinct=True),
                rating_avg=Avg("ratings__value"),
            )
            .prefetch_related("authors")
        )

    def _book_stats(self, book):
        """Счётчики перечитываются из БД, поэтому ответ всегда показывает
        состояние после изменения, а не из старого queryset."""
        fresh = Book.objects.filter(pk=book.pk).annotate(
            likes_count=Count("likes"), rating_avg=Avg("ratings__value")
        ).get()
        return {"likes_count": fresh.likes_count, "rating_avg": fresh.rating_avg}

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """POST лайкает, DELETE снимает. Оба идемпотентны: повтор не создаёт
        вторую строку и не падает, а возвращает текущее состояние книги."""
        book = self.get_object()
        if request.method == "DELETE":
            BookLike.objects.filter(book=book, user=request.user).delete()
            liked = False
        else:
            BookLike.objects.get_or_create(book=book, user=request.user)
            liked = True

        payload = {"liked": liked, "book": book.pk}
        payload.update(self._book_stats(book))
        return Response(payload, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["get", "post", "delete"],
        permission_classes=[IsAuthenticated],
        url_path="rating",
    )
    def rating(self, request, pk=None):
        """GET показывает мою оценку, POST ставит или меняет её, DELETE убирает.
        Книга берётся из URL, оценка от одного пользователя одна."""
        book = self.get_object()
        if request.method == "DELETE":
            BookRating.objects.filter(book=book, user=request.user).delete()
            payload = {"rated": False, "book": book.pk}
            payload.update(self._book_stats(book))
            return Response(payload, status=status.HTTP_200_OK)

        if request.method == "GET":
            rating = BookRating.objects.filter(book=book, user=request.user).first()
            if rating is None:
                return Response({"detail": "Оценка не найдена."}, status=status.HTTP_404_NOT_FOUND)
            return Response(BookRatingSerializer(rating).data, status=status.HTTP_200_OK)

        serializer = BookRatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rating, created = BookRating.objects.update_or_create(
            book=book,
            user=request.user,
            defaults={"value": serializer.validated_data["value"]},
        )
        payload = BookRatingSerializer(rating).data
        payload["rated"] = True
        payload.update(self._book_stats(book))
        return Response(payload, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class BookRatingViewSet(viewsets.ModelViewSet):
    """/api/ratings/ — мои оценки. Нужны, чтобы перечислить их все разом,
    чего не даёт вложенный путь /api/books/<id>/rating/."""

    serializer_class = BookRatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BookRating.objects.filter(user=self.request.user).select_related("book")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
