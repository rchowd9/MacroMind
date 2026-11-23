from dataclasses import dataclass, field

@dataclass
class Food:
    name: str
    calories_per_100g: float = 0
    protein_per_100g: float = 0
    carbohydrates_per_100g: float = 0
    fats_per_100g: float = 0
    fiber_per_100g: float = 0
    sugar_per_100g: float = 0
    sodium_mg_per_100g: float = 0
    vitamins: dict[str, float] = field(default_factory=dict)

def calculating_total_calories(list_of_food: list["Food"]) -> float:
    total_calories = 0.0
    for food in list_of_food:
        total_calories += food.calories_per_100g
    return total_calories

    
