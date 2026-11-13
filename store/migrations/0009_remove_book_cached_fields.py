# Remove cached likes_count and rating_avg fields from Book
# Counts are now computed dynamically via annotate() in the queryset.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0008_bookrating_rating_value_1_to_5"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="book",
            name="likes_count",
        ),
        migrations.RemoveField(
            model_name="book",
            name="rating_avg",
        ),
    ]
