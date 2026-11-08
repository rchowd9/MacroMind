class RecommendationService:

    @staticmethod
    def recommend_food(user, foods):

        remaining = (
            user.goal.calorie_goal -
            user.total_calories()
        )

        suitable_foods = []

        for food in foods:
            if food.calories <= remaining:
                suitable_foods.append(food)

        return sorted(
            suitable_foods,
            key=lambda x: x.protein,
            reverse=True
        )[:5]