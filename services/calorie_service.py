class CalorieService:

    @staticmethod
    def calories_remaining(user):
        if not user.goal:
            return None

        return user.goal.calorie_goal - user.total_calories()

    @staticmethod
    def goal_met(user):
        if not user.goal:
            return False

        return user.total_calories() >= user.goal.calorie_goal