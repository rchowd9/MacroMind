from django.core.validators import MinValueValidator
from django.db import models


class Food(models.Model):
    name = models.CharField(max_length=120, unique=True)
    calories_per_100g = models.DecimalField(max_digits=7, decimal_places=2, validators=[MinValueValidator(0)])
    protein_per_100g = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    carbs_per_100g = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    fats_per_100g = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Goal(models.Model):
    calorie_goal = models.PositiveIntegerField(default=2000)
    protein_goal = models.PositiveIntegerField(default=150)
    carbs_goal = models.PositiveIntegerField(default=250)
    fats_goal = models.PositiveIntegerField(default=65)

    class Meta:
        verbose_name = "daily goal"


class UserProfile(models.Model):
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)


class MealEntry(models.Model):
    food = models.ForeignKey(Food, on_delete=models.PROTECT, related_name="meal_entries")
    quantity_grams = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    date = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]


class WeeklyCalorieGoal(models.Model):
    week_start = models.DateField(unique=True)
    calorie_goal = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["week_start"]

    def __str__(self) -> str:
        return f"{self.week_start.isoformat()}: {self.calorie_goal} kcal"


class MealTemplate(models.Model):
    name = models.CharField(max_length=120, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class MealTemplateItem(models.Model):
    template = models.ForeignKey(MealTemplate, on_delete=models.CASCADE, related_name="items")
    food = models.ForeignKey(Food, on_delete=models.PROTECT, related_name="template_items")
    quantity_grams = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    class Meta:
        ordering = ["id"]
