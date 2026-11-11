from django.urls import path

from api import views


urlpatterns = [
    path("api/health/", views.health, name="health"),
    path("api/foods/", views.foods, name="foods"),
    path("api/goal/", views.goal, name="goal"),
    path("api/profile/", views.profile, name="profile"),
    path("api/meals/", views.meals, name="meals"),
    path("api/meals/<int:meal_id>/", views.meal_detail, name="meal-detail"),
]
