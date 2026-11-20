from datetime import date
from typing import Any

import requests


class APIError(Exception):
    """An API request failed or returned an invalid response."""


class MacroMindAPI:
    def __init__(self, base_url: str, token: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def list_foods(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/foods/")

    def create_food(self, food: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/foods/", json=food)

    def delete_food(self, food_id: int) -> None:
        self._request("DELETE", f"/api/foods/{food_id}/")

    def get_goal(self) -> dict[str, Any]:
        return self._request("GET", "/api/goal/")

    def update_goal(self, goal: dict[str, Any]) -> dict[str, Any]:
        return self._request("PUT", "/api/goal/", json=goal)

    def get_profile(self) -> dict[str, Any]:
        return self._request("GET", "/api/profile/")

    def update_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        return self._request("PUT", "/api/profile/", json=profile)

    def list_meals(self, tracking_date: date) -> list[dict[str, Any]]:
        return self._request("GET", "/api/meals/", params={"date": tracking_date.isoformat()})

    def list_meals_between(self, start_date: date, end_date: date) -> list[dict[str, Any]]:
        return self._request(
            "GET",
            "/api/meals/",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

    def create_meal(self, food_id: int, quantity_grams: float, tracking_date: date) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/meals/",
            json={
                "food_id": food_id,
                "quantity_grams": quantity_grams,
                "date": tracking_date.isoformat(),
            },
        )

    def delete_meal(self, meal_id: int) -> None:
        self._request("DELETE", f"/api/meals/{meal_id}/")

    def get_weekly_calorie_goal(self, week_start: date) -> dict[str, Any]:
        return self._request(
            "GET",
            "/api/weekly-calorie-goal/",
            params={"week_start": week_start.isoformat()},
        )

    def update_weekly_calorie_goal(self, week_start: date, calorie_goal: int) -> dict[str, Any]:
        return self._request(
            "PUT",
            "/api/weekly-calorie-goal/",
            json={
                "week_start": week_start.isoformat(),
                "calorie_goal": calorie_goal,
            },
        )

    def list_meal_templates(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/meal-templates/")

    def create_meal_template(self, template: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/meal-templates/", json=template)

    def delete_meal_template(self, template_id: int) -> None:
        self._request("DELETE", f"/api/meal-templates/{template_id}/")

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        try:
            response = requests.request(
                method,
                f"{self.base_url}{path}",
                headers=headers,
                timeout=self.timeout,
                **kwargs,
            )
        except requests.RequestException as error:
            raise APIError(f"Backend is unreachable at {self.base_url}: {error}") from error

        if not response.ok:
            try:
                detail = response.json().get("error", response.text)
            except ValueError:
                detail = response.text
            raise APIError(f"Backend returned {response.status_code}: {detail}")
        if response.status_code == 204:
            return None
        try:
            return response.json()
        except ValueError as error:
            raise APIError("Backend returned an invalid JSON response.") from error
