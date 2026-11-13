from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from store.models import Author, Book, BookLike


class BookFilteringTest(APITestCase):
    """Тесты фильтрации книг через DjangoFilterBackend."""

    def setUp(self):
        self.author1 = Author.objects.create(name="Альфа")
        self.author2 = Author.objects.create(name="Бета")
        self.book1 = Book.objects.create(name="Книга А", price=Decimal("100.00"))
        self.book1.authors.add(self.author1)
        self.book2 = Book.objects.create(name="Книга Б", price=Decimal("200.00"))
        self.book2.authors.add(self.author2)
        self.book3 = Book.objects.create(name="Книга В", price=Decimal("100.00"))
        self.list_url = "/api/books/"

    def test_filter_by_price(self):
        """Фильтрация по exact-значению price."""
        response = self.client.get(self.list_url, {"price": "100.00"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        for item in response.data["results"]:
            self.assertEqual(Decimal(item["price"]), Decimal("100.00"))

    def test_filter_by_author(self):
        """Фильтрация по exact-author id через M2M."""
        response = self.client.get(self.list_url, {"authors": self.author1.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Книга А")

    def test_filter_no_match(self):
        """Фильтр, который не совпадает ни с одной книгой, возвращает пустой список."""
        response = self.client.get(self.list_url, {"price": "999.99"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)


class BookOrderingTest(APITestCase):
    """Тесты сортировки книг через OrderingFilter."""

    def setUp(self):
        self.author1 = Author.objects.create(name="Альфа")
        self.author2 = Author.objects.create(name="Бета")
        self.book1 = Book.objects.create(name="Книга 1", price=Decimal("300.00"))
        self.book1.authors.add(self.author1)
        self.book2 = Book.objects.create(name="Книга 2", price=Decimal("100.00"))
        self.book2.authors.add(self.author2)
        self.book3 = Book.objects.create(name="Книга 3", price=Decimal("200.00"))
        self.list_url = "/api/books/"

    def test_default_ordering(self):
        """По умолчанию сортировка по возрастанию цены."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prices = [Decimal(b["price"]) for b in response.data["results"]]
        self.assertEqual(prices, sorted(prices))

    def test_ordering_by_price_asc(self):
        """Сортировка по цене по возрастанию."""
        response = self.client.get(self.list_url, {"ordering": "price"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prices = [Decimal(b["price"]) for b in response.data["results"]]
        self.assertEqual(prices, [Decimal("100.00"), Decimal("200.00"), Decimal("300.00")])

    def test_ordering_by_price_desc(self):
        """Сортировка по цене по убыванию."""
        response = self.client.get(self.list_url, {"ordering": "-price"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prices = [Decimal(b["price"]) for b in response.data["results"]]
        self.assertEqual(prices, [Decimal("300.00"), Decimal("200.00"), Decimal("100.00")])

    def test_ordering_by_author_name(self):
        """Сортировка по аннотации author_name: Альфа, Бета, книга без автора."""
        response = self.client.get(self.list_url, {"ordering": "author_name"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [b["name"] for b in response.data["results"]]
        self.assertEqual(titles, ["Книга 1", "Книга 2", "Книга 3"])

    def test_ordering_by_author_name_desc(self):
        """Сортировка по аннотации author_name по убыванию."""
        response = self.client.get(self.list_url, {"ordering": "-author_name"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [b["name"] for b in response.data["results"]]
        # PostgreSQL: NULL первыми при DESC, затем Бета > Альфа
        self.assertEqual(titles[0], "Книга 3")
        self.assertEqual(titles[1], "Книга 2")
        self.assertEqual(titles[2], "Книга 1")

    def test_ordering_field_allowed(self):
        """ordering_fields ограничивает допустимые поля."""
        response = self.client.get(self.list_url, {"ordering": "nonexistent"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # DRF возвращает 200 и игнорирует недопустимое поле — это стандартное поведение
        self.assertEqual(len(response.data["results"]), 3)


class ApiRootViewTest(APITestCase):
    """Индексная страница / отдаёт книги с количеством лайков."""

    ROOT_URL = "/"

    def setUp(self):
        self.user = User.objects.create_user(username="reader", password="pw12345")
        self.book = Book.objects.create(name="Книга", price=Decimal("50.00"))

    def test_root_page_ok(self):
        response = self.client.get(self.ROOT_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_context_books_have_likes_count(self):
        BookLike.objects.create(book=self.book, user=self.user)

        response = self.client.get(self.ROOT_URL)

        books = list(response.context["books"])
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0].likes_count, 1)

    def test_zero_likes_without_like_rows(self):
        response = self.client.get(self.ROOT_URL)

        books = list(response.context["books"])
        self.assertEqual(books[0].likes_count, 0)

    def test_likes_count_matches_api(self):
        """Страница и API /api/books/ показывают одинаковое число лайков."""
        other = User.objects.create_user(username="second", password="pw12345")
        BookLike.objects.create(book=self.book, user=self.user)
        BookLike.objects.create(book=self.book, user=other)

        page = self.client.get(self.ROOT_URL)
        api = self.client.get("/api/books/")

        page_count = list(page.context["books"])[0].likes_count
        api_count = api.data["results"][0]["likes_count"]
        self.assertEqual(page_count, api_count)
