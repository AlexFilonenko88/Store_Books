from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from store.models import Author, Book

LIST_URL = "/api/books/"


class BookApiCreateTest(APITestCase):
    """POST /api/books/ — создание книги."""

    def setUp(self):
        self.author = Author.objects.create(name="Лев Толстой")

    def test_create_book(self):
        response = self.client.post(LIST_URL, {"name": "Новая книга", "price": "100.50"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        book = Book.objects.get(name="Новая книга")
        self.assertEqual(book.price, Decimal("100.50"))
        self.assertEqual(response.data["id"], book.pk)
        self.assertEqual(response.data["authors"], [])

    def test_create_book_with_authors(self):
        response = self.client.post(
            LIST_URL,
            {"name": "Война и мир", "price": "890.00", "authors": [self.author.pk]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        book = Book.objects.get(name="Война и мир")
        self.assertEqual(list(book.authors.all()), [self.author])
        self.assertEqual(response.data["authors"], [self.author.pk])

    def test_create_book_missing_price(self):
        response = self.client.post(LIST_URL, {"name": "Без цены"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", response.data)
        self.assertEqual(Book.objects.count(), 0)

    def test_create_book_invalid_name(self):
        response = self.client.post(LIST_URL, {"name": "", "price": "10.00"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
        self.assertEqual(Book.objects.count(), 0)

    def test_create_book_invalid_author(self):
        response = self.client.post(
            LIST_URL, {"name": "Книга", "price": "10.00", "authors": [999999]}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("authors", response.data)


class BookApiReadTest(APITestCase):
    """GET /api/books/ и /api/books/<id>/ — чтение."""

    def setUp(self):
        self.author = Author.objects.create(name="Лев Толстой")
        self.book = Book.objects.create(name="Война и мир", price=Decimal("890.00"))
        self.book.authors.add(self.author)

    def test_list_books(self):
        response = self.client.get(LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Война и мир")

    def test_retrieve_book(self):
        response = self.client.get(f"{LIST_URL}{self.book.pk}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.book.pk)
        self.assertEqual(response.data["name"], "Война и мир")
        self.assertEqual(Decimal(response.data["price"]), Decimal("890.00"))
        self.assertEqual(response.data["authors"], [self.author.pk])

    def test_retrieve_missing_book(self):
        response = self.client.get(f"{LIST_URL}999999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_urls_resolve(self):
        self.assertEqual(reverse("book-list"), LIST_URL)
        self.assertEqual(reverse("book-detail", args=[self.book.pk]), f"{LIST_URL}{self.book.pk}/")


class BookApiUpdateTest(APITestCase):
    """PUT и PATCH /api/books/<id>/ — обновление."""

    def setUp(self):
        self.old_author = Author.objects.create(name="Старый автор")
        self.new_author = Author.objects.create(name="Новый автор")
        self.book = Book.objects.create(name="Война и мир", price=Decimal("890.00"))
        self.book.authors.add(self.old_author)
        self.detail_url = f"{LIST_URL}{self.book.pk}/"

    def test_update_book(self):
        response = self.client.put(
            self.detail_url, {"name": "Обновлённая", "price": "500.00"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.name, "Обновлённая")
        self.assertEqual(self.book.price, Decimal("500.00"))

    def test_update_book_authors(self):
        response = self.client.put(
            self.detail_url,
            {"name": "Война и мир", "price": "890.00", "authors": [self.new_author.pk]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(self.book.authors.all()), [self.new_author])

    def test_partial_update_book(self):
        response = self.client.patch(self.detail_url, {"price": "111.11"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.price, Decimal("111.11"))
        self.assertEqual(self.book.name, "Война и мир")

    def test_update_book_invalid_price(self):
        response = self.client.patch(self.detail_url, {"price": "не число"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", response.data)
        self.book.refresh_from_db()
        self.assertEqual(self.book.price, Decimal("890.00"))

    def test_update_missing_book(self):
        response = self.client.put(f"{LIST_URL}999999/", {"name": "Нет такой", "price": "1.00"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class BookApiDeleteTest(APITestCase):
    """DELETE /api/books/<id>/ — удаление."""

    def setUp(self):
        self.book = Book.objects.create(name="Война и мир", price=Decimal("890.00"))
        self.detail_url = f"{LIST_URL}{self.book.pk}/"

    def test_delete_book(self):
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Book.objects.count(), 0)

    def test_delete_book_keeps_author(self):
        author = Author.objects.create(name="Лев Толстой")
        self.book.authors.add(author)

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(Author.objects.filter(pk=author.pk).exists())

    def test_delete_missing_book(self):
        response = self.client.delete(f"{LIST_URL}999999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_already_deleted_book(self):
        self.client.delete(self.detail_url)

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
