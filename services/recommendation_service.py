from typing import Any


def recommend_protein_foods(
    foods: list[dict[str, Any]],
    *,
    calories_remaining: float,
    protein_remaining: float,
    limit: int = 3,
) -> list[dict[str, Any]]:
    if calories_remaining <= 0 or protein_remaining <= 0 or limit <= 0:
        return []

    recommendations = []
    for food in foods:
        calories_per_100g = float(food["calories_per_100g"])
        protein_per_100g = float(food["protein_per_100g"])
        if calories_per_100g < 0 or protein_per_100g <= 0:
            continue

        quantity_grams = min(100.0, protein_remaining * 100 / protein_per_100g)
        if calories_per_100g > 0:
            quantity_grams = min(
                quantity_grams, calories_remaining * 100 / calories_per_100g
            )
        if quantity_grams <= 0:
            continue

        calories = calories_per_100g * quantity_grams / 100
        protein = protein_per_100g * quantity_grams / 100
        recommendations.append(
            {
                "food": food,
                "quantity_grams": quantity_grams,
                "calories": calories,
                "protein": protein,
                "protein_per_calorie": protein_per_100g / max(calories_per_100g, 1),
            }
        )

    return sorted(
        recommendations,
        key=lambda item: (item["protein_per_calorie"], item["protein"]),
        reverse=True,
    )[:limit]
