from decimal import Decimal

from django.db import DatabaseError, IntegrityError, transaction
from django.test import TestCase

from store.models import Book


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
