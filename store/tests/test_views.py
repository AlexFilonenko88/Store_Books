from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from store.models import Book


class BookApiTest(APITestCase):
    """Интеграционные тесты CRUD-эндпоинтов /api/books/."""

    def setUp(self):
        self.book = Book.objects.create(name="Война и мир", price=Decimal("890.00"))
        self.list_url = "/api/books/"
        self.detail_url = f"/api/books/{self.book.pk}/"

    def test_list_books(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Война и мир")

    def test_retrieve_book(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.book.pk)
        self.assertEqual(Decimal(response.data["price"]), Decimal("890.00"))

    def test_retrieve_missing_book(self):
        response = self.client.get("/api/books/999999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_book(self):
        data = {"name": "Новая книга", "price": "100.50"}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 2)
        self.assertEqual(Book.objects.get(name="Новая книга").price, Decimal("100.50"))

    def test_create_book_invalid(self):
        response = self.client.post(self.list_url, {"name": ""}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_update_book(self):
        response = self.client.put(
            self.detail_url,
            {"name": "Обновлённая", "price": "500.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.name, "Обновлённая")
        self.assertEqual(self.book.price, Decimal("500.00"))

    def test_partial_update_book(self):
        response = self.client.patch(
            self.detail_url, {"price": "111.11"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.price, Decimal("111.11"))
        self.assertEqual(self.book.name, "Война и мир")

    def test_delete_book(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Book.objects.count(), 0)

    def test_urls_resolve(self):
        """Маршруты роутера существуют."""
        self.assertEqual(reverse("book-list"), "/api/books/")
        self.assertEqual(
            reverse("book-detail", args=[self.book.pk]), f"/api/books/{self.book.pk}/"
        )
