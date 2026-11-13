import os
from datetime import date, timedelta

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from services.api_client import APIError, MacroMindAPI
from services.recommendation_service import recommend_protein_foods


def setting(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, os.getenv(name, default)))
    except StreamlitSecretNotFoundError:
        return os.getenv(name, default)


st.set_page_config(page_title="MacroMind", page_icon="🥗", layout="wide")
st.title("MacroMind")
st.caption("Track what you eat, understand your macros, and work toward your daily goal.")

api = MacroMindAPI(
    base_url=setting("MACROMIND_API_URL", "http://127.0.0.1:8000"),
    token=setting("MACROMIND_API_TOKEN"),
)

try:
    goal = api.get_goal()
    profile = api.get_profile()
except APIError as error:
    st.error(f"Could not load MacroMind data: {error}")
    st.info(
        "Start the Django backend with `python manage.py runserver` and configure "
        "`MACROMIND_API_URL` and `MACROMIND_API_TOKEN`."
    )
    st.stop()

with st.sidebar:
    st.header("Daily plan")
    selected_date = st.date_input("Tracking date", value=date.today())
    with st.form("goal_form"):
        st.subheader("Daily goals")
        calorie_goal = st.number_input("Calories", min_value=1, max_value=10000, value=goal["calorie_goal"], step=50)
        protein_goal = st.number_input("Protein (g)", min_value=1, max_value=1000, value=goal["protein_goal"], step=5)
        carbs_goal = st.number_input("Carbohydrates (g)", min_value=1, max_value=1000, value=goal["carbs_goal"], step=5)
        fats_goal = st.number_input("Fat (g)", min_value=1, max_value=1000, value=goal["fats_goal"], step=5)
        save_goal = st.form_submit_button("Save daily goals", use_container_width=True)
    with st.form("profile_form"):
        st.subheader("Personal measurements")
        weight_kg = st.number_input(
            "Weight (kg)",
            min_value=1.0,
            max_value=500.0,
            value=profile["weight_kg"] or 70.0,
            step=0.1,
        )
        height_cm = st.number_input(
            "Height (cm)",
            min_value=1.0,
            max_value=300.0,
            value=profile["height_cm"] or 170.0,
            step=0.1,
        )
        save_profile = st.form_submit_button("Save measurements", use_container_width=True)

try:
    foods = api.list_foods()
    meals = api.list_meals(selected_date)
    week_start = selected_date - timedelta(days=6)
    weekly_meals = api.list_meals_between(week_start, selected_date)
except APIError as error:
    st.error(f"Could not load MacroMind data: {error}")
    st.info(
        "Start the Django backend with `python manage.py runserver` and configure "
        "`MACROMIND_API_URL` and `MACROMIND_API_TOKEN`."
    )
    st.stop()

if save_goal:
    try:
        goal = api.update_goal(
            {
                "calorie_goal": calorie_goal,
                "protein_goal": protein_goal,
                "carbs_goal": carbs_goal,
                "fats_goal": fats_goal,
            }
        )
        st.sidebar.success("Daily goals saved.")
    except APIError as error:
        st.sidebar.error(f"Could not save goals: {error}")

if save_profile:
    try:
        profile = api.update_profile({"weight_kg": weight_kg, "height_cm": height_cm})
        st.sidebar.success("Personal measurements saved.")
    except APIError as error:
        st.sidebar.error(f"Could not save measurements: {error}")

with st.sidebar:
    st.caption(
        f"Current plan: {goal['calorie_goal']} kcal · "
        f"{goal['protein_goal']} g protein · {goal['carbs_goal']} g carbs · "
        f"{goal['fats_goal']} g fat"
    )

calories = sum(meal["totals"]["calories"] for meal in meals)
protein = sum(meal["totals"]["protein"] for meal in meals)
carbs = sum(meal["totals"]["carbs"] for meal in meals)
fats = sum(meal["totals"]["fats"] for meal in meals)
remaining = goal["calorie_goal"] - calories
protein_remaining = goal["protein_goal"] - protein
protein_recommendations = recommend_protein_foods(
    foods,
    calories_remaining=max(remaining, 0),
    protein_remaining=max(protein_remaining, 0),
)

calorie_col, protein_col, carbs_col, fats_col = st.columns(4)
calorie_col.metric(
    "Calories",
    f"{calories:,.0f} kcal",
    f"{remaining:,.0f} kcal remaining" if remaining >= 0 else f"{abs(remaining):,.0f} kcal over",
)
protein_col.metric("Protein", f"{protein:.1f} g", f"of {goal['protein_goal']} g")
carbs_col.metric("Carbohydrates", f"{carbs:.1f} g", f"of {goal['carbs_goal']} g")
fats_col.metric("Fat", f"{fats:.1f} g", f"of {goal['fats_goal']} g")
st.progress(min(calories / goal["calorie_goal"], 1.0), text="Daily calorie goal")

log_tab, foods_tab, meals_tab, insights_tab = st.tabs(
    ["Log food", "Food library", "Today's meals", "Weekly insights"]
)

with log_tab:
    st.subheader("Add food to your day")
    st.markdown("#### Smart protein picks")
    if protein_recommendations:
        st.caption("Portions are sized to fit your remaining calorie and protein goals.")
        for recommendation in protein_recommendations:
            food = recommendation["food"]
            recommendation_col, action_col = st.columns([3, 1])
            recommendation_col.markdown(
                f"**{food['name']}** · {recommendation['quantity_grams']:.0f} g"
            )
            recommendation_col.caption(
                f"{recommendation['calories']:.0f} kcal · "
                f"{recommendation['protein']:.1f} g protein"
            )
            if action_col.button(
                "Log pick", key=f"recommend_{food['id']}", use_container_width=True
            ):
                try:
                    api.create_meal(
                        food["id"], recommendation["quantity_grams"], selected_date
                    )
                    st.success(f"Added {food['name']} to your day.")
                    st.rerun()
                except APIError as error:
                    st.error(f"Could not add food: {error}")
    else:
        st.caption("Your calorie or protein goal is met, or no suitable foods are saved yet.")

    if foods:
        food_options = {food["name"]: food for food in foods}
        with st.form("log_food_form"):
            food_name = st.selectbox("Food", list(food_options))
            quantity = st.number_input("Amount (grams)", min_value=1.0, max_value=5000.0, value=100.0, step=10.0)
            add_meal = st.form_submit_button("Add to daily log", type="primary")
        if add_meal:
            try:
                api.create_meal(food_options[food_name]["id"], quantity, selected_date)
                st.success(f"Added {quantity:g} g of {food_name}.")
                st.rerun()
            except APIError as error:
                st.error(f"Could not add food: {error}")
    else:
        st.info("Add foods in the Food library tab before logging a meal.")

    st.subheader("Add a food")
    with st.form("create_food_form", clear_on_submit=True):
        new_name = st.text_input("Food name")
        food_col1, food_col2 = st.columns(2)
        new_calories = food_col1.number_input("Calories per 100 g", min_value=0.0, max_value=1000.0, value=100.0, step=1.0)
        new_protein = food_col2.number_input("Protein per 100 g (g)", min_value=0.0, max_value=100.0, value=5.0, step=0.5)
        new_carbs = food_col1.number_input("Carbohydrates per 100 g (g)", min_value=0.0, max_value=100.0, value=10.0, step=0.5)
        new_fats = food_col2.number_input("Fat per 100 g (g)", min_value=0.0, max_value=100.0, value=3.0, step=0.5)
        create_food = st.form_submit_button("Save food")
    if create_food:
        try:
            api.create_food(
                {
                    "name": new_name,
                    "calories_per_100g": new_calories,
                    "protein_per_100g": new_protein,
                    "carbs_per_100g": new_carbs,
                    "fats_per_100g": new_fats,
                }
            )
            st.success(f"Saved {new_name}.")
            st.rerun()
        except APIError as error:
            st.error(f"Could not save food: {error}")

with foods_tab:
    st.subheader("Food library")
    st.caption("Nutrition values are per 100 g. Add or adjust foods to match your own labels.")
    if foods:
        st.dataframe(
            [
                {
                    "Food": food["name"],
                    "Calories": food["calories_per_100g"],
                    "Protein (g)": food["protein_per_100g"],
                    "Carbs (g)": food["carbs_per_100g"],
                    "Fat (g)": food["fats_per_100g"],
                }
                for food in foods
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("Your food library is empty.")

with meals_tab:
    st.subheader(f"Meals for {selected_date:%B %d, %Y}")
    if not meals:
        st.info("Nothing logged for this day yet.")
    for meal in meals:
        with st.container(border=True):
            meal_col, nutrition_col, action_col = st.columns([3, 3, 1])
            meal_col.markdown(f"**{meal['food']['name']}**")
            meal_col.caption(f"{meal['quantity_grams']:g} g")
            meal_col.caption(
                f"{meal['totals']['calories']:.0f} kcal · "
                f"P {meal['totals']['protein']:.1f} g · "
                f"C {meal['totals']['carbs']:.1f} g · "
                f"F {meal['totals']['fats']:.1f} g"
            )
            if action_col.button("Remove", key=f"remove_{meal['id']}"):
                try:
                    api.delete_meal(meal["id"])
                    st.rerun()
                except APIError as error:
                    st.error(f"Could not remove meal: {error}")

with insights_tab:
    st.subheader(f"Seven-day nutrition trend through {selected_date:%B %d}")
    daily_totals = {
        (week_start + timedelta(days=offset)).isoformat(): {
            "calories": 0.0,
            "protein": 0.0,
            "carbs": 0.0,
            "fats": 0.0,
        }
        for offset in range(7)
    }
    for meal in weekly_meals:
        day_totals = daily_totals[meal["date"]]
        for nutrient in day_totals:
            day_totals[nutrient] += meal["totals"][nutrient]

    trend_rows = [
        {
            "Date": date.fromisoformat(day).strftime("%a %b %d"),
            "Calories": totals["calories"],
            "Protein (g)": totals["protein"],
            "Carbs (g)": totals["carbs"],
            "Fat (g)": totals["fats"],
        }
        for day, totals in daily_totals.items()
    ]
    average_calories = sum(row["Calories"] for row in trend_rows) / 7
    days_on_target = sum(
        row["Calories"] > 0 and row["Calories"] <= goal["calorie_goal"]
        for row in trend_rows
    )
    average_protein = sum(row["Protein (g)"] for row in trend_rows) / 7

    average_col, target_col, protein_average_col = st.columns(3)
    average_col.metric("Average calories / day", f"{average_calories:,.0f} kcal")
    target_col.metric("Days within calorie goal", f"{days_on_target} / 7")
    protein_average_col.metric("Average protein / day", f"{average_protein:.1f} g")
    st.bar_chart(trend_rows, x="Date", y="Calories")
    st.dataframe(trend_rows, hide_index=True, use_container_width=True)
