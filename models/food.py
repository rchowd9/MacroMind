from dataclasses import dataclass 

@dataclass
class Food:
    name: str
    calories: int
    serving_size: str
    calories: int
    protein: float
    carbohydrates: float
    fats: float
    vitamins: dict
    dietaryFiber: float

def calculating_total_calories(list_of_food):
    total_calories = 0
    for food in list_of_food:
        total_calories += food.calories
        return total_calories

    
