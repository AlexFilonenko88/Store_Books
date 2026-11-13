from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError, transaction
from django.test import TestCase

from store.models import Author, Book, BookLike, BookRating


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


class BookLikeModelTest(TestCase):
    """BookLike: один лайк от одного пользователя на одну книгу."""

    def setUp(self):
        self.user = User.objects.create_user(username="reader", password="pw12345")
        self.book = Book.objects.create(name="Книга", price=Decimal("50.00"))

    def test_like_created_and_readable_both_ways(self):
        """Лайк читается и со стороны книги, и со стороны пользователя."""
        like = BookLike.objects.create(book=self.book, user=self.user)

        self.assertEqual(list(self.book.likes.all()), [like])
        self.assertEqual(list(self.user.liked_books.all()), [like])

    def test_created_at_is_set_automatically(self):
        """created_at заполняется при создании."""
        like = BookLike.objects.create(book=self.book, user=self.user)

        self.assertIsNotNone(like.created_at)

    def test_duplicate_like_rejected(self):
        """UniqueConstraint(book, user): второй лайк от того же пользователя невозможен."""
        BookLike.objects.create(book=self.book, user=self.user)

        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                BookLike.objects.create(book=self.book, user=self.user)

    def test_same_user_can_like_different_books(self):
        """Ограничение действует в паре (book, user), а не по одному пользователю."""
        other = Book.objects.create(name="Другая книга", price=Decimal("10.00"))

        BookLike.objects.create(book=self.book, user=self.user)
        BookLike.objects.create(book=other, user=self.user)

        self.assertEqual(BookLike.objects.count(), 2)

    def test_different_users_can_like_same_book(self):
        """Два пользователя могут лайкнуть одну книгу."""
        user2 = User.objects.create_user(username="second", password="pw12345")

        BookLike.objects.create(book=self.book, user=self.user)
        BookLike.objects.create(book=self.book, user=user2)

        self.assertEqual(self.book.likes.count(), 2)

    def test_deleting_book_deletes_likes(self):
        """on_delete=CASCADE по book: удаление книги убирает её лайки."""
        like = BookLike.objects.create(book=self.book, user=self.user)

        self.book.delete()

        self.assertFalse(BookLike.objects.filter(pk=like.pk).exists())

    def test_deleting_user_deletes_likes(self):
        """on_delete=CASCADE по user: удаление пользователя убирает его лайки."""
        like = BookLike.objects.create(book=self.book, user=self.user)

        self.user.delete()

        self.assertFalse(BookLike.objects.filter(pk=like.pk).exists())

    def test_str_mentions_user_and_book(self):
        like = BookLike.objects.create(book=self.book, user=self.user)

        self.assertEqual(str(like), "reader -> Книга")


class BookRatingModelTest(TestCase):
    """BookRating: одна оценка 1..5 от одного пользователя на одну книгу."""

    def setUp(self):
        self.user = User.objects.create_user(username="reader", password="pw12345")
        self.book = Book.objects.create(name="Книга", price=Decimal("50.00"))

    def test_rating_created_and_readable_both_ways(self):
        """Оценка читается и со стороны книги, и со стороны пользователя."""
        rating = BookRating.objects.create(book=self.book, user=self.user, value=4)

        self.assertEqual(list(self.book.ratings.all()), [rating])
        self.assertEqual(list(self.user.book_ratings.all()), [rating])

    def test_duplicate_rating_rejected(self):
        """UniqueConstraint(book, user): вторая оценка невозможна, её нужно обновлять."""
        BookRating.objects.create(book=self.book, user=self.user, value=4)

        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                BookRating.objects.create(book=self.book, user=self.user, value=5)

    def test_validation_accepts_border_values(self):
        """Граничные значения 1 и 5 проходят full_clean."""
        for value in (1, 5):
            rating = BookRating(book=self.book, user=self.user, value=value)
            rating.full_clean(exclude=["created_at"])

    def test_validation_rejects_value_below_range(self):
        """0 недопустим."""
        rating = BookRating(book=self.book, user=self.user, value=0)

        with self.assertRaises(ValidationError) as ctx:
            rating.full_clean(exclude=["created_at"])
        self.assertIn("value", ctx.exception.message_dict)

    def test_validation_rejects_value_above_range(self):
        """6 недопустим."""
        rating = BookRating(book=self.book, user=self.user, value=6)

        with self.assertRaises(ValidationError) as ctx:
            rating.full_clean(exclude=["created_at"])
        self.assertIn("value", ctx.exception.message_dict)

    def test_database_enforces_value_range(self):
        """CheckConstraint(value BETWEEN 1 AND 5) на уровне БД: create(6) падает."""
        with transaction.atomic():
            with self.assertRaises(Exception):
                BookRating.objects.create(book=self.book, user=self.user, value=6)

    def test_deleting_book_deletes_ratings(self):
        """on_delete=CASCADE по book: удаление книги убирает её оценки."""
        rating = BookRating.objects.create(book=self.book, user=self.user, value=3)

        self.book.delete()

        self.assertFalse(BookRating.objects.filter(pk=rating.pk).exists())

    def test_deleting_user_deletes_ratings(self):
        """on_delete=CASCADE по user: удаление пользователя убирает его оценки."""
        rating = BookRating.objects.create(book=self.book, user=self.user, value=3)

        self.user.delete()

        self.assertFalse(BookRating.objects.filter(pk=rating.pk).exists())

    def test_str_mentions_value(self):
        rating = BookRating.objects.create(book=self.book, user=self.user, value=4)

        self.assertEqual(str(rating), "reader -> Книга: 4")
