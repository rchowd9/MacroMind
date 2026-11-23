from dataclasses import dataclass
from models.food import Food

@dataclass
class Meal:
    food: Food
    quantity: float

    def total_calories(self):
        return self.food.calories_per_100g * self.quantity / 100

    def total_protein(self):
        return self.food.protein_per_100g * self.quantity / 100

    def total_carbs(self):
        return self.food.carbohydrates_per_100g * self.quantity / 100

    def total_fats(self):
        return self.food.fats_per_100g * self.quantity / 100

    def total_fiber(self):
        return self.food.fiber_per_100g * self.quantity / 100

    def total_sugar(self):
        return self.food.sugar_per_100g * self.quantity / 100

    def total_sodium_mg(self):
        return self.food.sodium_mg_per_100g * self.quantity / 100