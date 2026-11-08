from dataclasses import dataclass
from models.food import Food

@dataclass
class Meal:
    food: Food
    quantity: float

    def total_calories(self):
        return self.food.calories_per_gram() * self.quantity

    def total_protein(self):
        return (self.food.protein / self.food.serving_size) * self.quantity

    def total_carbs(self):
        return (self.food.carbs / self.food.serving_size) * self.quantity

    def total_fats(self):
        return (self.food.fats / self.food.serving_size) * self.quantity