from django.contrib import admin

from .models import Author, Book, BookLike, BookRating


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "owner")
    search_fields = ("name",)
    list_filter = ("authors",)
    raw_id_fields = ("owner",)


class BookLikeInline(admin.TabularInline):
    model = BookLike
    readonly_fields = ("user", "created_at")
    extra = 0


class BookRatingInline(admin.TabularInline):
    model = BookRating
    readonly_fields = ("user", "value", "created_at")
    extra = 0


@admin.register(BookLike)
class BookLikeAdmin(admin.ModelAdmin):
    list_display = ("book", "user", "created_at")
    list_filter = ("book", "user")
    readonly_fields = ("book", "user", "created_at")


@admin.register(BookRating)
class BookRatingAdmin(admin.ModelAdmin):
    list_display = ("book", "user", "value", "created_at")
    list_filter = ("book", "user", "value")
    readonly_fields = ("book", "user", "value", "created_at")
