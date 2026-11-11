import json

from django.test import TestCase, override_settings

from api.models import Food, MealEntry


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
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["name"], "Apple")
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
        self.assertEqual(len(self.client.get("/api/meals/?date=2026-11-09").json()), 1)
        self.assertEqual(len(self.client.get("/api/meals/?date=2026-11-10").json()), 0)

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
