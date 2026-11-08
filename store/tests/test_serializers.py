from decimal import Decimal

from django.test import SimpleTestCase

from store.serializers import BookSerializer


class BookSerializerValidationTest(SimpleTestCase):
    """Валидация входных данных через сериализатор (без обращения к БД)."""

    def test_valid_data(self):
        serializer = BookSerializer(data={"name": "Книга", "price": "123.45"})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["price"], Decimal("123.45"))

    def test_name_required(self):
        serializer = BookSerializer(data={"price": "10.00"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_price_required(self):
        serializer = BookSerializer(data={"name": "Книга"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("price", serializer.errors)

    def test_price_must_be_decimal(self):
        serializer = BookSerializer(data={"name": "Книга", "price": "не число"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("price", serializer.errors)

    def test_name_too_long(self):
        serializer = BookSerializer(data={"name": "а" * 201, "price": "10.00"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_output_representation(self):
        class FakeBook:
            id = 1
            name = "Книга"
            price = Decimal("10.00")
            authors = []

        data = BookSerializer(instance=FakeBook()).data
        self.assertEqual(data, {"id": 1, "name": "Книга", "authors": [], "price": "10.00"})
