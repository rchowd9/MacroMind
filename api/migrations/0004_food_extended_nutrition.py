from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0003_weeklycaloriegoal_mealtemplate_mealtemplateitem"),
    ]

    operations = [
        migrations.AddField(
            model_name="food",
            name="fiber_per_100g",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="food",
            name="sodium_mg_per_100g",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=7, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="food",
            name="sugar_per_100g",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
