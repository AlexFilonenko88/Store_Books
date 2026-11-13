from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
class Author(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        verbose_name = "Автор"
        verbose_name_plural = "Авторы"

    def __str__(self):
        return self.name


class Book(models.Model):
    name = models.CharField(max_length=200)
    authors = models.ManyToManyField(Author, related_name="books", blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="books",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Книга"
        verbose_name_plural = "Книги"

    def __str__(self):
        return self.name


class BookLike(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="liked_books",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Лайк"
        verbose_name_plural = "Лайки"
        constraints = [
            models.UniqueConstraint(
                fields=["book", "user"], name="uniq_book_like"
            ),
        ]

    def __str__(self):
        return f"{self.user} -> {self.book}"


class BookRating(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="book_ratings",
    )
    value = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Рейтинг"
        verbose_name_plural = "Рейтинги"
        constraints = [
            models.UniqueConstraint(
                fields=["book", "user"], name="uniq_book_rating"
            ),
            models.CheckConstraint(
                condition=models.Q(value__gte=1) & models.Q(value__lte=5),
                name="rating_value_1_to_5",
            ),
        ]

    def __str__(self):
        return f"{self.user} -> {self.book}: {self.value}"
