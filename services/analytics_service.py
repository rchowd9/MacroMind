class AnalyticsService:

    @staticmethod
    def macro_breakdown(user):

        protein = sum(
            meal.total_protein()
            for meal in user.meals
        )

        carbs = sum(
            meal.total_carbs()
            for meal in user.meals
        )

        fats = sum(
            meal.total_fats()
            for meal in user.meals
        )

        return {
            "protein": protein,
            "carbs": carbs,
            "fats": fats
        }