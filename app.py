import os
from datetime import date

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from services.api_client import APIError, MacroMindAPI


def setting(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, os.getenv(name, default)))
    except StreamlitSecretNotFoundError:
        return os.getenv(name, default)


st.set_page_config(page_title="MacroMind", page_icon="🥗", layout="wide")
st.title("MacroMind")
st.caption("Track what you eat, understand your macros, and work toward your daily goal.")

with st.sidebar:
    st.header("Daily plan")
    selected_date = st.date_input("Tracking date", value=date.today())
    with st.form("goal_form"):
        st.subheader("Daily goals")
        calorie_goal = st.number_input("Calories", min_value=1, max_value=10000, value=2000, step=50)
        protein_goal = st.number_input("Protein (g)", min_value=1, max_value=1000, value=150, step=5)
        carbs_goal = st.number_input("Carbohydrates (g)", min_value=1, max_value=1000, value=250, step=5)
        fats_goal = st.number_input("Fat (g)", min_value=1, max_value=1000, value=65, step=5)
        save_goal = st.form_submit_button("Save daily goals", use_container_width=True)

api = MacroMindAPI(
    base_url=setting("MACROMIND_API_URL", "http://127.0.0.1:8000"),
    token=setting("MACROMIND_API_TOKEN"),
)

try:
    foods = api.list_foods()
    goal = api.get_goal()
    meals = api.list_meals(selected_date)
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

log_tab, foods_tab, meals_tab = st.tabs(["Log food", "Food library", "Today's meals"])

with log_tab:
    st.subheader("Add food to your day")
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
    st.subheader(f"Meals for {selected_date:%B %-d, %Y}")
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
