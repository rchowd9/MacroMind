import hmac
import json
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import wraps
from typing import Any, Callable

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.models import Food, Goal, MealEntry


def api_endpoint(view: Callable[..., JsonResponse]) -> Callable[..., JsonResponse]:
    @csrf_exempt
    @wraps(view)
    def wrapped(request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        configured_token = settings.MACROMIND_API_TOKEN
        if not configured_token:
            return JsonResponse({"error": "The backend API token is not configured."}, status=503)
        supplied_token = request.headers.get("Authorization", "")
        expected_token = f"Bearer {configured_token}"
        if not hmac.compare_digest(supplied_token, expected_token):
            return JsonResponse({"error": "A valid bearer token is required."}, status=401)
        return view(request, *args, **kwargs)

    return wrapped


def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


def food_data(food: Food) -> dict[str, Any]:
    return {
        "id": food.id,
        "name": food.name,
        "calories_per_100g": float(food.calories_per_100g),
        "protein_per_100g": float(food.protein_per_100g),
        "carbs_per_100g": float(food.carbs_per_100g),
        "fats_per_100g": float(food.fats_per_100g),
    }


def goal_data(goal: Goal) -> dict[str, int]:
    return {
        "calorie_goal": goal.calorie_goal,
        "protein_goal": goal.protein_goal,
        "carbs_goal": goal.carbs_goal,
        "fats_goal": goal.fats_goal,
    }


def meal_data(meal: MealEntry) -> dict[str, Any]:
    factor = meal.quantity_grams / Decimal("100")
    food = meal.food
    return {
        "id": meal.id,
        "date": meal.date.isoformat(),
        "quantity_grams": float(meal.quantity_grams),
        "food": food_data(food),
        "totals": {
            "calories": float(food.calories_per_100g * factor),
            "protein": float(food.protein_per_100g * factor),
            "carbs": float(food.carbs_per_100g * factor),
            "fats": float(food.fats_per_100g * factor),
        },
    }


def parse_body(request: HttpRequest) -> dict[str, Any]:
    try:
        value = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("Request body must be valid JSON.") from error
    if not isinstance(value, dict):
        raise ValueError("Request body must be a JSON object.")
    return value


def decimal_value(data: dict[str, Any], field: str, *, minimum: Decimal = Decimal("0")) -> Decimal:
    try:
        value = Decimal(str(data[field]))
    except (KeyError, InvalidOperation, TypeError, ValueError) as error:
        raise ValueError(f"{field} must be a number.") from error
    if not value.is_finite() or value < minimum:
        raise ValueError(f"{field} must be at least {minimum}.")
    return value


@api_endpoint
def foods(request: HttpRequest) -> JsonResponse:
    if request.method == "GET":
        return JsonResponse([food_data(food) for food in Food.objects.all()], safe=False)
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed."}, status=405)
    try:
        data = parse_body(request)
        name = data.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name is required.")
        food = Food.objects.create(
            name=name.strip(),
            calories_per_100g=decimal_value(data, "calories_per_100g"),
            protein_per_100g=decimal_value(data, "protein_per_100g"),
            carbs_per_100g=decimal_value(data, "carbs_per_100g"),
            fats_per_100g=decimal_value(data, "fats_per_100g"),
        )
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    except Exception as error:
        if getattr(error, "is_integrity_error", False):
            return JsonResponse({"error": "A food with that name already exists."}, status=400)
        raise
    return JsonResponse(food_data(food), status=201)


@api_endpoint
def goal(request: HttpRequest) -> JsonResponse:
    current_goal, _ = Goal.objects.get_or_create(pk=1)
    if request.method == "GET":
        return JsonResponse(goal_data(current_goal))
    if request.method != "PUT":
        return JsonResponse({"error": "Method not allowed."}, status=405)
    try:
        data = parse_body(request)
        values = {
            "calorie_goal": data["calorie_goal"],
            "protein_goal": data["protein_goal"],
            "carbs_goal": data["carbs_goal"],
            "fats_goal": data["fats_goal"],
        }
        for field, value in values.items():
            if isinstance(value, bool) or not str(value).isdigit() or int(value) <= 0:
                raise ValueError(f"{field} must be a positive whole number.")
        for field, value in values.items():
            setattr(current_goal, field, int(value))
        current_goal.save()
    except (KeyError, ValueError) as error:
        return JsonResponse({"error": str(error)}, status=400)
    return JsonResponse(goal_data(current_goal))


@api_endpoint
def meals(request: HttpRequest) -> JsonResponse:
    if request.method == "GET":
        raw_date = request.GET.get("date", date.today().isoformat())
        try:
            tracking_date = date.fromisoformat(raw_date)
        except ValueError:
            return JsonResponse({"error": "date must use YYYY-MM-DD format."}, status=400)
        return JsonResponse(
            [meal_data(meal) for meal in MealEntry.objects.filter(date=tracking_date).select_related("food")],
            safe=False,
        )
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed."}, status=405)
    try:
        data = parse_body(request)
        food = Food.objects.get(pk=int(data["food_id"]))
        tracking_date = date.fromisoformat(str(data["date"]))
        quantity = decimal_value(data, "quantity_grams", minimum=Decimal("0.01"))
        meal = MealEntry.objects.create(food=food, date=tracking_date, quantity_grams=quantity)
    except (KeyError, TypeError, ValueError, Food.DoesNotExist, InvalidOperation) as error:
        return JsonResponse({"error": "Provide a valid food_id, date, and positive quantity_grams."}, status=400)
    return JsonResponse(meal_data(meal), status=201)


@api_endpoint
def meal_detail(request: HttpRequest, meal_id: int) -> JsonResponse:
    if request.method != "DELETE":
        return JsonResponse({"error": "Method not allowed."}, status=405)
    try:
        meal = MealEntry.objects.get(pk=meal_id)
    except MealEntry.DoesNotExist:
        return JsonResponse({"error": "Meal entry not found."}, status=404)
    meal.delete()
    return JsonResponse({}, status=204)
