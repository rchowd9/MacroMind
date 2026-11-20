from django.core.validators import MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0002_userprofile"),
    ]

    operations = [
        migrations.CreateModel(
            name="WeeklyCalorieGoal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("week_start", models.DateField(unique=True)),
                ("calorie_goal", models.PositiveIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["week_start"]},
        ),
        migrations.CreateModel(
            name="MealTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="MealTemplateItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity_grams", models.DecimalField(decimal_places=2, max_digits=8, validators=[MinValueValidator(0.01)])),
                ("food", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="template_items", to="api.food")),
                ("template", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="api.mealtemplate")),
            ],
            options={"ordering": ["id"]},
        ),
    ]
