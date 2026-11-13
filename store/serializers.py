from rest_framework import serializers

from .models import Book, BookRating


class BookSerializer(serializers.ModelSerializer):
    """Книга с динамически вычисленными счётчиками лайков и средней оценки."""

    likes_count = serializers.SerializerMethodField(read_only=True)
    rating_avg = serializers.SerializerMethodField(read_only=True, allow_null=True)

    class Meta:
        model = Book
        fields = ["id", "name", "authors", "price", "likes_count", "rating_avg"]

    def get_likes_count(self, obj):
        return getattr(obj, "likes_count", 0)

    def get_rating_avg(self, obj):
        return getattr(obj, "rating_avg", None)


class BookRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookRating
        fields = ["id", "book", "user", "value", "created_at"]
        read_only_fields = ["id", "book", "user", "created_at"]
