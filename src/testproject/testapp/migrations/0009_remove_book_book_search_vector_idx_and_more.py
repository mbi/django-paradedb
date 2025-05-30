# Generated by Django 5.1.6 on 2025-04-06 12:24

from django.db import migrations
import django


class Migration(migrations.Migration):
    dependencies = [
        ("testapp", "0008_bookreview"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="book",
            name="book_search_vector_idx",
        ),
        migrations.RunSQL(
            sql="""
              ALTER TABLE testapp_book ADD COLUMN vector_column tsvector GENERATED ALWAYS AS (
                setweight(to_tsvector('english', coalesce(description, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(title,'')), 'B')
              ) STORED;
            """,
            reverse_sql="""
              ALTER TABLE testapp_book DROP COLUMN vector_column;
            """,
            state_operations=[
                migrations.AddField(
                    model_name="book",
                    name="vector_column",
                    field=django.contrib.postgres.search.SearchVectorField(null=True),
                ),
            ],
        ),
    ]
