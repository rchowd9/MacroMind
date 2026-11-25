from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0004_food_extended_nutrition"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="mealentry",
            index=models.Index(
                fields=["date", "created_at"],
                name="api_meal_day_created_idx",
            ),
        ),
    ]
