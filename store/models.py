from django.conf import settings
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
