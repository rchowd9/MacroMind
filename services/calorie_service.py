class CalorieService:

    @staticmethod
    def calories_remaining(user):
        goal = getattr(user, "goal", None)
        if goal is None:
            return None

        calorie_goal = getattr(goal, "calorie_goal", None)
        if calorie_goal is None:
            return None

        total_calories = getattr(user, "total_calories", lambda: 0)()
        return float(calorie_goal) - float(total_calories)

    @staticmethod
    def goal_met(user):
        goal = getattr(user, "goal", None)
        if goal is None:
            return False

        calorie_goal = getattr(goal, "calorie_goal", None)
        if calorie_goal is None:
            return False

        return float(getattr(user, "total_calories", lambda: 0)()) >= float(calorie_goal)