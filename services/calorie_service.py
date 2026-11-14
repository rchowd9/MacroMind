class CalorieService:

    @staticmethod
    def calories_remaining(user):
        goal = getattr(user, "goal", None)
        if isinstance(goal, dict):
            calorie_goal = goal.get("calorie_goal")
        else:
            calorie_goal = getattr(goal, "calorie_goal", None)
        if calorie_goal is None:
            return None

        total_calories = getattr(user, "total_calories", lambda: 0)() if not isinstance(user, dict) else user.get("total_calories", 0)
        return float(calorie_goal) - float(total_calories)

    @staticmethod
    def goal_met(user):
        goal = getattr(user, "goal", None)
        if isinstance(goal, dict):
            calorie_goal = goal.get("calorie_goal")
        else:
            calorie_goal = getattr(goal, "calorie_goal", None)
        if calorie_goal is None:
            return False

        total_calories = getattr(user, "total_calories", lambda: 0)() if not isinstance(user, dict) else user.get("total_calories", 0)
        return float(total_calories) >= float(calorie_goal)