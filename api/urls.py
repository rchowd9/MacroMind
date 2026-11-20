from django.urls import path

from api import views


urlpatterns = [
    path("api/health/", views.health, name="health"),
    path("api/foods/", views.foods, name="foods"),
    path("api/foods/<int:food_id>/", views.food_detail, name="food-detail"),
    path("api/goal/", views.goal, name="goal"),
    path("api/profile/", views.profile, name="profile"),
    path("api/meals/", views.meals, name="meals"),
    path("api/meals/<int:meal_id>/", views.meal_detail, name="meal-detail"),
    path("api/weekly-calorie-goal/", views.weekly_calorie_goal, name="weekly-calorie-goal"),
    path("api/meal-templates/", views.meal_templates, name="meal-templates"),
    path("api/meal-templates/<int:template_id>/", views.meal_template_detail, name="meal-template-detail"),
]
