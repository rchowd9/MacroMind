class AnalyticsService:

    @staticmethod
    def macro_breakdown(user):
        meals = getattr(user, "meals", []) or []

        protein = 0.0
        carbs = 0.0
        fats = 0.0

        for meal in meals:
            if hasattr(meal, "total_protein"):
                protein += float(meal.total_protein())
            elif isinstance(meal, dict):
                protein += float(meal.get("protein", 0) or 0)

            if hasattr(meal, "total_carbs"):
                carbs += float(meal.total_carbs())
            elif isinstance(meal, dict):
                carbs += float(meal.get("carbs", 0) or 0)

            if hasattr(meal, "total_fats"):
                fats += float(meal.total_fats())
            elif isinstance(meal, dict):
                fats += float(meal.get("fats", 0) or 0)

        return {
            "protein": protein,
            "carbs": carbs,
            "fats": fats,
        }