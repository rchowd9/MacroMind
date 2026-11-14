from typing import Any


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _food_value(food: dict[str, Any], key: str) -> float:
    if not isinstance(food, dict):
        return 0.0
    return _to_float(food.get(key))


def recommend_foods(
    foods: list[dict[str, Any]],
    *,
    calories_remaining: float,
    protein_remaining: float,
    limit: int = 3,
    max_quantity_grams: float = 100.0,
) -> list[dict[str, Any]]:
    if calories_remaining <= 0 or protein_remaining <= 0 or limit <= 0:
        return []

    recommendations: list[dict[str, Any]] = []
    for food in foods:
        calories_per_100g = _food_value(food, "calories_per_100g")
        protein_per_100g = _food_value(food, "protein_per_100g")
        if calories_per_100g < 0 or protein_per_100g <= 0:
            continue

        quantity_grams = min(float(max_quantity_grams), protein_remaining * 100 / protein_per_100g)
        if calories_per_100g > 0:
            quantity_grams = min(
                quantity_grams,
                calories_remaining * 100 / calories_per_100g,
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


def recommend_protein_foods(
    foods: list[dict[str, Any]],
    *,
    calories_remaining: float,
    protein_remaining: float,
    limit: int = 3,
) -> list[dict[str, Any]]:
    return recommend_foods(
        foods,
        calories_remaining=calories_remaining,
        protein_remaining=protein_remaining,
        limit=limit,
    )
