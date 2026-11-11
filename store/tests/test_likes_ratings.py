from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from store.models import Author, Book, BookLike, BookRating

LIST_URL = "/api/books/"


def detail_url(book):
    return f"{LIST_URL}{book.pk}/"


def like_url(book):
    return f"{detail_url(book)}like/"


def rating_url(book):
    return f"{detail_url(book)}rating/"


class AnonymousAccessTest(APITestCase):
    """Без авторизации книги читаются как раньше, а лайки и оценки закрыты."""

    def setUp(self):
        self.book = Book.objects.create(name="Книга", price=Decimal("50.00"))

    def test_book_list_still_public(self):
        response = self.client.get(LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_anonymous_cannot_like(self):
        response = self.client.post(like_url(self.book))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(BookLike.objects.count(), 0)

    def test_anonymous_cannot_rate(self):
        response = self.client.post(rating_url(self.book), {"value": 5}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(BookRating.objects.count(), 0)


class BookLikeApiTest(APITestCase):
    """/api/books/<id>/like/: POST лайкает, DELETE снимает."""

    def setUp(self):
        self.user = User.objects.create_user(username="reader", password="pw12345")
        self.book = Book.objects.create(name="Книга", price=Decimal("50.00"))
        self.client.force_authenticate(user=self.user)

    def test_like_creates_row_and_counts(self):
        response = self.client.post(like_url(self.book))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["liked"], True)
        self.assertEqual(response.data["likes_count"], 1)
        self.assertEqual(BookLike.objects.filter(book=self.book, user=self.user).count(), 1)

    def test_repeat_like_is_idempotent(self):
        self.client.post(like_url(self.book))

        response = self.client.post(like_url(self.book))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["likes_count"], 1)
        self.assertEqual(BookLike.objects.count(), 1)

    def test_unlike_removes_row(self):
        BookLike.objects.create(book=self.book, user=self.user)

        response = self.client.delete(like_url(self.book))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["liked"], False)
        self.assertEqual(response.data["likes_count"], 0)
        self.assertEqual(BookLike.objects.count(), 0)

    def test_unlike_without_like_is_idempotent(self):
        response = self.client.delete(like_url(self.book))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["likes_count"], 0)

    def test_like_counts_every_user(self):
        other = User.objects.create_user(username="second", password="pw12345")
        BookLike.objects.create(book=self.book, user=other)

        response = self.client.post(like_url(self.book))

        self.assertEqual(response.data["likes_count"], 2)

    def test_like_missing_book(self):
        response = self.client.post("/api/books/999999/like/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_like_after_book_deleted(self):
        self.book.delete()

        response = self.client.post(like_url(self.book))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_on_like_is_not_allowed(self):
        response = self.client.get(like_url(self.book))

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class BookRatingApiTest(APITestCase):
    """/api/books/<id>/rating/: POST ставит или меняет оценку, GET и DELETE по своей."""

    def setUp(self):
        self.user = User.objects.create_user(username="reader", password="pw12345")
        self.book = Book.objects.create(name="Книга", price=Decimal("50.00"))
        self.client.force_authenticate(user=self.user)

    def test_rating_created(self):
        response = self.client.post(rating_url(self.book), {"value": 4}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["value"], 4)
        self.assertEqual(response.data["book"], self.book.pk)
        self.assertEqual(BookRating.objects.get(book=self.book, user=self.user).value, 4)

    def test_second_rating_updates_instead_of_duplicating(self):
        self.client.post(rating_url(self.book), {"value": 4}, format="json")

        response = self.client.post(rating_url(self.book), {"value": 5}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["value"], 5)
        self.assertEqual(BookRating.objects.filter(book=self.book, user=self.user).count(), 1)

    def test_rating_avg_recounted_after_update(self):
        other = User.objects.create_user(username="second", password="pw12345")
        BookRating.objects.create(book=self.book, user=other, value=1)

        self.client.post(rating_url(self.book), {"value": 5}, format="json")

        response = self.client.get(rating_url(self.book))
        self.assertEqual(response.data["value"], 5)
        list_response = self.client.get(LIST_URL)
        self.assertAlmostEqual(list_response.data[0]["rating_avg"], 3.0)

    def test_get_own_rating(self):
        BookRating.objects.create(book=self.book, user=self.user, value=3)

        response = self.client.get(rating_url(self.book))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["value"], 3)

    def test_get_missing_rating_is_404(self):
        response = self.client.get(rating_url(self.book))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_own_rating(self):
        BookRating.objects.create(book=self.book, user=self.user, value=3)

        response = self.client.delete(rating_url(self.book))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rated"], False)
        self.assertEqual(BookRating.objects.count(), 0)

    def test_rating_rejects_value_above_range(self):
        response = self.client.post(rating_url(self.book), {"value": 6}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("value", response.data)
        self.assertEqual(BookRating.objects.count(), 0)

    def test_rating_rejects_value_below_range(self):
        response = self.client.post(rating_url(self.book), {"value": 0}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("value", response.data)

    def test_rating_requires_value(self):
        response = self.client.post(rating_url(self.book), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("value", response.data)

    def test_other_users_rating_is_not_returned(self):
        other = User.objects.create_user(username="second", password="pw12345")
        BookRating.objects.create(book=self.book, user=other, value=1)

        response = self.client.get(rating_url(self.book))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_rating_on_missing_book(self):
        response = self.client.post("/api/books/999999/rating/", {"value": 4}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_body_cannot_forge_book_or_user(self):
        other = User.objects.create_user(username="second", password="pw12345")
        other_book = Book.objects.create(name="Чужая", price=Decimal("10.00"))

        response = self.client.post(
            rating_url(self.book),
            {"value": 5, "book": other_book.pk, "user": other.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        rating = BookRating.objects.get()
        self.assertEqual(rating.book, self.book)
        self.assertEqual(rating.user, self.user)


class MyRatingsApiTest(APITestCase):
    """/api/ratings/ — список, чтение и удаление оценок текущего пользователя."""

    RATINGS_URL = "/api/ratings/"

    def setUp(self):
        self.user = User.objects.create_user(username="reader", password="pw12345")
        self.other = User.objects.create_user(username="second", password="pw12345")
        self.book = Book.objects.create(name="Книга", price=Decimal("50.00"))
        self.own = BookRating.objects.create(book=self.book, user=self.user, value=4)
        self.foreign = BookRating.objects.create(book=self.book, user=self.other, value=1)
        self.client.force_authenticate(user=self.user)

    def test_list_shows_only_own_ratings(self):
        response = self.client.get(self.RATINGS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([r["id"] for r in response.data], [self.own.pk])

    def test_anonymous_cannot_list_ratings(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.RATINGS_URL)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_foreign_rating_is_404(self):
        response = self.client.get(f"{self.RATINGS_URL}{self.foreign.pk}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_own_rating(self):
        response = self.client.delete(f"{self.RATINGS_URL}{self.own.pk}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(BookRating.objects.filter(pk=self.own.pk).exists())
        self.assertTrue(BookRating.objects.filter(pk=self.foreign.pk).exists())

    def test_delete_foreign_rating_is_404(self):
        response = self.client.delete(f"{self.RATINGS_URL}{self.foreign.pk}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(BookRating.objects.filter(pk=self.foreign.pk).exists())


class BookStatsInListTest(APITestCase):
    """Список книг отдаёт счётчики и умеет по ним сортировать."""

    def setUp(self):
        self.user = User.objects.create_user(username="reader", password="pw12345")
        self.other = User.objects.create_user(username="second", password="pw12345")
        self.plain = Book.objects.create(name="Без оценок", price=Decimal("10.00"))
        self.popular = Book.objects.create(name="Популярная", price=Decimal("20.00"))
        self.client.force_authenticate(user=self.user)

    def test_counters_present_and_zero_by_default(self):
        response = self.client.get(LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = next(b for b in response.data if b["name"] == "Без оценок")
        self.assertEqual(item["likes_count"], 0)
        self.assertIsNone(item["rating_avg"])

    def test_counters_follow_likes_and_ratings(self):
        BookLike.objects.create(book=self.popular, user=self.user)
        BookLike.objects.create(book=self.popular, user=self.other)
        BookRating.objects.create(book=self.popular, user=self.user, value=4)
        BookRating.objects.create(book=self.popular, user=self.other, value=5)

        response = self.client.get(LIST_URL)

        item = next(b for b in response.data if b["name"] == "Популярная")
        self.assertEqual(item["likes_count"], 2)
        self.assertAlmostEqual(item["rating_avg"], 4.5)

    def test_m2m_authors_do_not_inflate_counters(self):
        """Count(distinct) прикрывает декартов join с authors."""
        for name in ("Альфа", "Бета", "Гамма"):
            self.popular.authors.add(Author.objects.create(name=name))
        BookLike.objects.create(book=self.popular, user=self.user)
        BookRating.objects.create(book=self.popular, user=self.user, value=4)

        response = self.client.get(LIST_URL)

        item = next(b for b in response.data if b["name"] == "Популярная")
        self.assertEqual(item["likes_count"], 1)
        self.assertAlmostEqual(item["rating_avg"], 4.0)

    def test_ordering_by_likes_count_desc(self):
        BookLike.objects.create(book=self.popular, user=self.user)

        response = self.client.get(LIST_URL, {"ordering": "-likes_count"})

        self.assertEqual([b["name"] for b in response.data], ["Популярная", "Без оценок"])

    def test_ordering_by_rating_avg_asc_puts_unrated_last(self):
        """Postgres ставит NULL последними при ASC: книга без оценок идёт после оценённой."""
        BookRating.objects.create(book=self.popular, user=self.user, value=2)

        response = self.client.get(LIST_URL, {"ordering": "rating_avg"})

        self.assertEqual([b["name"] for b in response.data], ["Популярная", "Без оценок"])

    def test_ordering_by_rating_avg_desc(self):
        BookRating.objects.create(book=self.popular, user=self.user, value=2)
        BookRating.objects.create(book=self.plain, user=self.other, value=4)

        response = self.client.get(LIST_URL, {"ordering": "-rating_avg"})

        self.assertEqual([b["name"] for b in response.data], ["Без оценок", "Популярная"])

    def test_list_does_not_issue_query_per_book(self):
        for i in range(5):
            book = Book.objects.create(name=f"К{i}", price=Decimal("1.00"))
            BookLike.objects.create(book=book, user=self.user)
            BookRating.objects.create(book=book, user=self.user, value=3)

        with self.assertNumQueries(2):
            response = self.client.get(LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 7)

    def test_like_then_list_shows_fresh_count(self):
        self.client.post(like_url(self.popular))

        response = self.client.get(LIST_URL)

        item = next(b for b in response.data if b["name"] == "Популярная")
        self.assertEqual(item["likes_count"], 1)
