from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BookRatingViewSet, BookViewSet

router = DefaultRouter()
router.register("books", BookViewSet, basename="book")
router.register("ratings", BookRatingViewSet, basename="bookrating")

urlpatterns = [
    path("", include(router.urls)),
]
