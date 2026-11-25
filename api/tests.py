import json

from django.test import TestCase, override_settings

from api.models import Food, MealEntry, MealTemplate, MealTemplateItem
from services.recommendation_service import recommend_protein_foods


@override_settings(MACROMIND_API_TOKEN="test-token")
class MacroMindAPITests(TestCase):
    def setUp(self) -> None:
        self.client.defaults["HTTP_AUTHORIZATION"] = "Bearer test-token"
        self.food = Food.objects.create(
            name="Oats",
            calories_per_100g=389,
            protein_per_100g=16.9,
            carbs_per_100g=66.3,
            fats_per_100g=6.9,
            fiber_per_100g=10.6,
            sugar_per_100g=0.99,
            sodium_mg_per_100g=2,
        )

    def test_api_requires_token(self) -> None:
        self.client.defaults.pop("HTTP_AUTHORIZATION")
        response = self.client.get("/api/foods/")
        self.assertEqual(response.status_code, 401)

    def test_create_and_list_food(self) -> None:
        response = self.client.post(
            "/api/foods/",
            data=json.dumps(
                {
                    "name": "Apple",
                    "calories_per_100g": 52,
                    "protein_per_100g": 0.3,
                    "carbs_per_100g": 13.8,
                    "fats_per_100g": 0.2,
                    "fiber_per_100g": 2.4,
                    "sugar_per_100g": 10.4,
                    "sodium_mg_per_100g": 1,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["name"], "Apple")
        self.assertEqual(response.json()["fiber_per_100g"], 2.4)
        self.assertEqual(response.json()["sugar_per_100g"], 10.4)
        self.assertEqual(response.json()["sodium_mg_per_100g"], 1)
        self.assertEqual(len(self.client.get("/api/foods/").json()), 2)

    def test_log_meal_calculates_nutrition_and_filters_by_date(self) -> None:
        response = self.client.post(
            "/api/meals/",
            data=json.dumps(
                {"food_id": self.food.id, "quantity_grams": 50, "date": "2026-11-09"}
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["totals"]["calories"], 194.5)
        self.assertEqual(response.json()["totals"]["protein"], 8.45)
        self.assertEqual(response.json()["totals"]["fiber"], 5.3)
        self.assertAlmostEqual(response.json()["totals"]["sugar"], 0.495)
        self.assertEqual(response.json()["totals"]["sodium_mg"], 1)
        self.assertEqual(len(self.client.get("/api/meals/?date=2026-11-09").json()), 1)
        self.assertEqual(len(self.client.get("/api/meals/?date=2026-11-10").json()), 0)

    def test_list_meals_for_date_range(self) -> None:
        MealEntry.objects.create(food=self.food, quantity_grams=100, date="2026-11-09")
        MealEntry.objects.create(food=self.food, quantity_grams=100, date="2026-11-11")
        response = self.client.get(
            "/api/meals/?start_date=2026-11-09&end_date=2026-11-10"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_reject_incomplete_or_reversed_meal_date_range(self) -> None:
        for query in (
            "?start_date=2026-11-09",
            "?start_date=2026-11-11&end_date=2026-11-09",
            "?start_date=invalid&end_date=2026-11-09",
        ):
            with self.subTest(query=query):
                self.assertEqual(
                    self.client.get(f"/api/meals/{query}").status_code, 400
                )

    def test_update_goal_and_reject_invalid_values(self) -> None:
        payload = {
            "calorie_goal": 2200,
            "protein_goal": 160,
            "carbs_goal": 240,
            "fats_goal": 70,
        }
        response = self.client.put(
            "/api/goal/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), payload)

        payload["calorie_goal"] = -1
        response = self.client.put(
            "/api/goal/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_get_and_update_personal_measurements(self) -> None:
        response = self.client.get("/api/profile/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"weight_kg": None, "height_cm": None})

        payload = {"weight_kg": 72.5, "height_cm": 175.2}
        response = self.client.put(
            "/api/profile/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), payload)
        self.assertEqual(self.client.get("/api/profile/").json(), payload)

    def test_reject_invalid_personal_measurements(self) -> None:
        for payload in (
            {"weight_kg": 0, "height_cm": 175},
            {"weight_kg": 72, "height_cm": 301},
            {"weight_kg": "not-a-number", "height_cm": 175},
        ):
            with self.subTest(payload=payload):
                response = self.client.put(
                    "/api/profile/", data=json.dumps(payload), content_type="application/json"
                )
                self.assertEqual(response.status_code, 400)

    def test_delete_meal(self) -> None:
        meal = MealEntry.objects.create(
            food=self.food, quantity_grams=100, date="2026-11-09"
        )
        response = self.client.delete(f"/api/meals/{meal.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(MealEntry.objects.filter(pk=meal.id).exists())

    def test_delete_unused_food_and_reject_used_food(self) -> None:
        unused = Food.objects.create(
            name="Banana",
            calories_per_100g=89,
            protein_per_100g=1.1,
            carbs_per_100g=22.8,
            fats_per_100g=0.3,
        )
        response = self.client.delete(f"/api/foods/{unused.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Food.objects.filter(pk=unused.id).exists())

        MealEntry.objects.create(
            food=self.food, quantity_grams=100, date="2026-11-09"
        )
        response = self.client.delete(f"/api/foods/{self.food.id}/")
        self.assertEqual(response.status_code, 409)
        self.assertTrue(Food.objects.filter(pk=self.food.id).exists())

    def test_protein_recommendations_fit_remaining_goals_and_rank_density(self) -> None:
        foods = [
            {"id": 1, "name": "Chicken", "calories_per_100g": 165, "protein_per_100g": 31},
            {"id": 2, "name": "Tofu", "calories_per_100g": 144, "protein_per_100g": 17},
        ]
        recommendations = recommend_protein_foods(
            foods, calories_remaining=100, protein_remaining=20
        )
        self.assertEqual(recommendations[0]["food"]["name"], "Chicken")
        for recommendation in recommendations:
            self.assertLessEqual(recommendation["calories"], 100)
            self.assertLessEqual(recommendation["protein"], 20)
            self.assertLessEqual(recommendation["quantity_grams"], 100)

    def test_protein_recommendations_stop_when_a_goal_is_met(self) -> None:
        foods = [
            {"id": 1, "name": "Chicken", "calories_per_100g": 165, "protein_per_100g": 31}
        ]
        self.assertEqual(
            recommend_protein_foods(
                foods, calories_remaining=100, protein_remaining=0
            ),
            [],
        )

    def test_weekly_calorie_goal_defaults_to_daily_goal_and_can_be_updated(self) -> None:
        response = self.client.get(
            "/api/weekly-calorie-goal/?week_start=2026-11-11"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["week_start"], "2026-11-09")
        self.assertEqual(response.json()["calorie_goal"], 14000)

        response = self.client.put(
            "/api/weekly-calorie-goal/",
            data=json.dumps(
                {"week_start": "2026-11-11", "calorie_goal": 12500}
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["week_start"], "2026-11-09")
        self.assertEqual(response.json()["calorie_goal"], 12500)

    def test_create_list_apply_and_delete_meal_template(self) -> None:
        apple = Food.objects.create(
            name="Apple",
            calories_per_100g=52,
            protein_per_100g=0.3,
            carbs_per_100g=13.8,
            fats_per_100g=0.2,
        )
        response = self.client.post(
            "/api/meal-templates/",
            data=json.dumps(
                {
                    "name": "Breakfast",
                    "items": [
                        {"food_id": self.food.id, "quantity_grams": 50},
                        {"food_id": apple.id, "quantity_grams": 200},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        template = response.json()
        self.assertEqual(template["name"], "Breakfast")
        self.assertEqual(len(template["items"]), 2)
        self.assertEqual(template["totals"]["calories"], 298.5)

        response = self.client.get("/api/meal-templates/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

        response = self.client.delete(f"/api/meal-templates/{template['id']}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(MealTemplate.objects.filter(pk=template["id"]).exists())

    def test_template_creation_rolls_back_when_an_item_is_invalid(self) -> None:
        response = self.client.post(
            "/api/meal-templates/",
            data=json.dumps(
                {
                    "name": "Broken template",
                    "items": [
                        {"food_id": self.food.id, "quantity_grams": 50},
                        {"food_id": 999999, "quantity_grams": 100},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(MealTemplate.objects.filter(name="Broken template").exists())

    def test_food_used_by_template_cannot_be_deleted(self) -> None:
        template = MealTemplate.objects.create(name="Oats template")
        MealTemplateItem.objects.create(
            template=template,
            food=self.food,
            quantity_grams=50,
        )
        response = self.client.delete(f"/api/foods/{self.food.id}/")
        self.assertEqual(response.status_code, 409)
        self.assertTrue(Food.objects.filter(pk=self.food.id).exists())
