from decimal import Decimal

from django.contrib.auth.models import User
from django.db import DatabaseError, IntegrityError, transaction
from django.test import TestCase

from store.models import Author, Book


class BookModelTest(TestCase):
    def setUp(self):
        self.book = Book.objects.create(name="Тестовая книга", price=Decimal("99.99"))

    def test_book_created(self):
        """Книга сохраняется в БД и доступна для чтения."""
        self.assertEqual(Book.objects.count(), 1)
        book = Book.objects.get(pk=self.book.pk)
        self.assertEqual(book.name, "Тестовая книга")
        self.assertEqual(book.price, Decimal("99.99"))

    def test_str_returns_name(self):
        """__str__ возвращает название книги."""
        self.assertEqual(str(self.book), "Тестовая книга")

    def test_price_precision(self):
        """DecimalField хранит два знака после запятой."""
        self.book.price = Decimal("10.5")
        self.book.save()
        self.book.refresh_from_db()
        self.assertEqual(self.book.price, Decimal("10.50"))

    def test_name_max_length(self):
        """Поле name ограничено 200 символами."""
        field = Book._meta.get_field("name")
        self.assertEqual(field.max_length, 200)

    def test_name_cannot_be_null(self):
        """Name обязателен: null нарушает ограничения схемы."""
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Book.objects.create(name=None, price=Decimal("1.00"))

    def test_price_cannot_exceed_max_digits(self):
        """Цена не может выйти за пределы max_digits=10, decimal_places=2."""
        with transaction.atomic():
            with self.assertRaises(DatabaseError):
                Book.objects.create(name="Слишком дорогая", price=Decimal("99999999999.00"))


class BookOwnerTest(TestCase):
    """Связь Book.owner -> User (внешний ключ)."""

    def setUp(self):
        self.owner = User.objects.create_user(username="reader", password="pw12345")
        self.book = Book.objects.create(
            name="Книга читателя", price=Decimal("50.00"), owner=self.owner
        )

    def test_owner_stored_and_readable(self):
        """Владелец книги сохраняется и читается через атрибут и обратную связь."""
        book = Book.objects.get(pk=self.book.pk)
        self.assertEqual(book.owner, self.owner)
        self.assertEqual(list(self.owner.books.all()), [book])

    def test_owner_optional(self):
        """owner необязателен: книга без владельца допустима."""
        book = Book.objects.create(name="Без владельца", price=Decimal("10.00"))
        self.assertIsNone(book.owner)

    def test_deleting_owner_deletes_books(self):
        """on_delete=CASCADE: удаление владельца удаляет его книги."""
        book_pk = self.book.pk
        self.owner.delete()
        self.assertFalse(Book.objects.filter(pk=book_pk).exists())

    def test_deleting_author_keeps_owner(self):
        """Удаление автора не затрагивает владельца книги."""
        author = Author.objects.create(name="Автор")
        self.book.authors.add(author)

        author.delete()

        self.book.refresh_from_db()
        self.assertEqual(self.book.owner, self.owner)
