from models.food import Food
from models.meal import Meal
from models.user import User
from models.goal import Goal

from services.calorie_service import (
    CalorieService
)

from services.analytics_service import (
    AnalyticsService
)

foods = [
    Food(
        "Chicken Breast",
        100,
        165,
        31,
        0,
        3.6
    ),
    Food(
        "Rice",
        100,
        130,
        2.7,
        28,
        0.3
    )
]

user = User(
    name="Riasat",
    age=21,
    weight=170,
    height=70
)

user.goal = Goal(
    calorie_goal=2500,
    protein_goal=180,
    carbs_goal=250,
    fats_goal=70
)

user.add_meal(
    Meal(
        foods[0],
        200
    )
)

user.add_meal(
    Meal(
        foods[1],
        300
    )
)

print("Calories:", user.total_calories())

print(
    "Remaining:",
    CalorieService.calories_remaining(user)
)

print(
    AnalyticsService.macro_breakdown(user)
)