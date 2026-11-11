from rest_framework import serializers

from .models import Book, BookRating


class BookSerializer(serializers.ModelSerializer):
    """Книга со счётчиками из аннотаций get_queryset.

    default нужен, чтобы сериализатор работал и на книге без аннотаций
    (например, сразу после POST), где атрибутов likes_count/rating_avg нет.
    """

    likes_count = serializers.IntegerField(read_only=True, default=0)
    rating_avg = serializers.FloatField(read_only=True, allow_null=True, default=None)

    class Meta:
        model = Book
        fields = ["id", "name", "authors", "price", "likes_count", "rating_avg"]


class BookRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookRating
        fields = ["id", "book", "user", "value", "created_at"]
        read_only_fields = ["id", "book", "user", "created_at"]
