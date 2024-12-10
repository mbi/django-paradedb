# Generated by Django 5.2 on 2024-12-10 08:39

import django.db.models.deletion
import paradedb.indexes
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Item",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=127)),
                ("description", models.TextField()),
                ("alt_name", models.CharField(blank=True, max_length=64, null=True)),
                ("rating", models.DecimalField(decimal_places=2, max_digits=3)),
            ],
            options={
                "verbose_name": "Item",
                "verbose_name_plural": "Items",
                "ordering": ("-pk",),
                "indexes": [
                    paradedb.indexes.BM25Index(
                        fields=["name", "alt_name", "description", "rating"],
                        name="item_idx",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="Review",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("added", models.DateTimeField(auto_now_add=True)),
                ("review", models.TextField()),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="testapp.item"
                    ),
                ),
            ],
            options={
                "verbose_name": "Review",
                "verbose_name_plural": "Reviews",
                "ordering": ["-added"],
                "indexes": [
                    paradedb.indexes.BM25Index(fields=["review"], name="review_idx")
                ],
            },
        ),
    ]
