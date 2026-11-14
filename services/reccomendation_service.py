from __future__ import annotations

from typing import Any

from services.recommendation_service import recommend_foods


class RecommendationService:
    """High-level recommendation helper for user-centric meal planning."""

    @staticmethod
    def recommend_food(user: Any, foods: list[Any], *, limit: int = 5) -> list[Any]:
        if not foods:
            return []

        goal = getattr(user, "goal", None)
        if goal is None:
            return []

        calorie_goal = getattr(goal, "calorie_goal", None)
        protein_goal = getattr(goal, "protein_goal", None)
        if calorie_goal is None or protein_goal is None:
            return []

        total_calories = getattr(user, "total_calories", lambda: 0)()
        total_protein = getattr(user, "total_protein", lambda: 0)()
        remaining_calories = max(float(calorie_goal) - float(total_calories), 0.0)
        remaining_protein = max(float(protein_goal) - float(total_protein), 0.0)

        normalized_foods: list[dict[str, Any]] = []
        for food in foods:
            if hasattr(food, "calories_per_100g"):
                normalized_foods.append(
                    {
                        "id": getattr(food, "id", None),
                        "name": getattr(food, "name", "Unknown"),
                        "calories_per_100g": food.calories_per_100g,
                        "protein_per_100g": getattr(food, "protein_per_100g", 0),
                    }
                )
            elif isinstance(food, dict):
                normalized_foods.append(food)

        return [
            item["food"]
            for item in recommend_foods(
                normalized_foods,
                calories_remaining=remaining_calories,
                protein_remaining=remaining_protein,
                limit=limit,
            )
        ]

    @staticmethod
    def recommend_high_protein_foods(user: Any, foods: list[Any], *, limit: int = 5) -> list[Any]:
        return RecommendationService.recommend_food(user, foods, limit=limit)
