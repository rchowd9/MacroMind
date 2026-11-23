import os
import csv
from io import StringIO
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
    with st.form("weekly_goal_form"):
        st.subheader("Weekly calorie budget")
        week_start = selected_date - timedelta(days=6)
        try:
            weekly_goal = api.get_weekly_calorie_goal(week_start)
        except APIError as error:
            st.error(f"Could not load weekly goal: {error}")
            weekly_goal = {"week_start": week_start.isoformat(), "calorie_goal": goal["calorie_goal"] * 7}
        weekly_calorie_goal = st.number_input(
            "Calories for 7-day period",
            min_value=1,
            max_value=70000,
            value=weekly_goal["calorie_goal"],
            step=500,
        )
        save_weekly_goal = st.form_submit_button("Save weekly calorie budget", use_container_width=True)

try:
    foods = api.list_foods()
    meals = api.list_meals(selected_date)
    week_start = selected_date - timedelta(days=6)
    weekly_meals = api.list_meals_between(week_start, selected_date)
    meal_templates = api.list_meal_templates()
    weekly_goal = api.get_weekly_calorie_goal(week_start)
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

if save_weekly_goal:
    try:
        weekly_goal = api.update_weekly_calorie_goal(week_start, int(weekly_calorie_goal))
        st.sidebar.success("Weekly calorie budget saved.")
    except APIError as error:
        st.sidebar.error(f"Could not save weekly goal: {error}")

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

log_tab, foods_tab, meals_tab, templates_tab, insights_tab = st.tabs(
    ["Log food", "Food library", "Today's meals", "Meal templates", "Weekly insights"]
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
        new_fiber = food_col1.number_input("Fiber per 100 g (g)", min_value=0.0, max_value=100.0, value=2.0, step=0.5)
        new_sugar = food_col2.number_input("Sugar per 100 g (g)", min_value=0.0, max_value=100.0, value=2.0, step=0.5)
        new_sodium = st.number_input("Sodium per 100 g (mg)", min_value=0.0, max_value=100000.0, value=100.0, step=10.0)
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
                    "fiber_per_100g": new_fiber,
                    "sugar_per_100g": new_sugar,
                    "sodium_mg_per_100g": new_sodium,
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
        food_rows = [
                {
                    "Food": food["name"],
                    "Calories": food["calories_per_100g"],
                    "Protein (g)": food["protein_per_100g"],
                    "Carbs (g)": food["carbs_per_100g"],
                    "Fat (g)": food["fats_per_100g"],
                    "Fiber (g)": food["fiber_per_100g"],
                    "Sugar (g)": food["sugar_per_100g"],
                    "Sodium (mg)": food["sodium_mg_per_100g"],
                }
                for food in foods
            ]
        st.dataframe(food_rows, hide_index=True, use_container_width=True)
        st.subheader("Remove a food")
        removable_foods = {
            food["name"]: food
            for food in foods
        }
        if removable_foods:
            remove_name = st.selectbox(
                "Food to remove",
                list(removable_foods),
                key="remove_food_name",
            )
            if st.button("Delete unused food", type="secondary"):
                try:
                    api.delete_food(removable_foods[remove_name]["id"])
                    st.success(f"Removed {remove_name} from the food library.")
                    st.rerun()
                except APIError as error:
                    st.error(f"Could not remove food: {error}")
        else:
            st.caption("No unused foods are available to remove.")
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
                f"F {meal['totals']['fats']:.1f} g · "
                f"Fiber {meal['totals']['fiber']:.1f} g · "
                f"Sugar {meal['totals']['sugar']:.1f} g · "
                f"Sodium {meal['totals']['sodium_mg']:.0f} mg"
            )
            if action_col.button("Remove", key=f"remove_{meal['id']}"):
                try:
                    api.delete_meal(meal["id"])
                    st.rerun()
                except APIError as error:
                    st.error(f"Could not remove meal: {error}")

with templates_tab:
    st.subheader("Reusable meal templates")
    if "template_draft" not in st.session_state:
        st.session_state.template_draft = []

    if foods:
        food_options = {food["name"]: food for food in foods}
        draft_col, quantity_col = st.columns([3, 1])
        draft_food_name = draft_col.selectbox(
            "Food for template",
            list(food_options),
            key="template_draft_food",
        )
        draft_quantity = quantity_col.number_input(
            "Amount (grams)",
            min_value=1.0,
            max_value=5000.0,
            value=100.0,
            step=10.0,
            key="template_draft_quantity",
        )
        if st.button("Add item to draft", use_container_width=True):
            st.session_state.template_draft.append(
                {
                    "food_id": food_options[draft_food_name]["id"],
                    "quantity_grams": draft_quantity,
                    "name": draft_food_name,
                }
            )
            st.rerun()

    if st.session_state.template_draft:
        st.caption("Draft items")
        for index, item in enumerate(st.session_state.template_draft):
            draft_item_col, remove_draft_col = st.columns([4, 1])
            draft_item_col.markdown(f"{item['name']} — {item['quantity_grams']:g} g")
            if remove_draft_col.button("Remove", key=f"remove_template_draft_{index}"):
                st.session_state.template_draft.pop(index)
                st.rerun()

        template_name = st.text_input("Template name", key="template_name")
        if st.button("Save template", type="primary"):
            if not template_name.strip():
                st.error("Enter a template name.")
            else:
                try:
                    api.create_meal_template(
                        {
                            "name": template_name,
                            "items": [
                                {
                                    "food_id": item["food_id"],
                                    "quantity_grams": item["quantity_grams"],
                                }
                                for item in st.session_state.template_draft
                            ],
                        }
                    )
                    st.session_state.template_draft = []
                    st.success(f"Saved template {template_name}.")
                    st.rerun()
                except APIError as error:
                    st.error(f"Could not save template: {error}")
    else:
        st.caption("Add at least one food item to create a template.")

    if meal_templates:
        st.divider()
        for template in meal_templates:
            with st.container(border=True):
                template_col, apply_col, delete_col = st.columns([3, 1, 1])
                template_col.markdown(f"**{template['name']}**")
                item_summary = ", ".join(
                    f"{item['food']['name']} {item['quantity_grams']:g} g"
                    for item in template["items"]
                )
                template_col.caption(
                    f"{item_summary} · {template['totals']['calories']:.0f} kcal"
                )
                if apply_col.button("Apply", key=f"apply_template_{template['id']}"):
                    try:
                        for item in template["items"]:
                            api.create_meal(
                                item["food"]["id"],
                                item["quantity_grams"],
                                selected_date,
                            )
                        st.success(f"Applied {template['name']} to {selected_date.isoformat()}.")
                        st.rerun()
                    except APIError as error:
                        st.error(f"Could not apply template: {error}")
                if delete_col.button("Delete", key=f"delete_template_{template['id']}"):
                    try:
                        api.delete_meal_template(template["id"])
                        st.success(f"Deleted template {template['name']}.")
                        st.rerun()
                    except APIError as error:
                        st.error(f"Could not delete template: {error}")
    else:
        st.info("No meal templates saved yet.")

with insights_tab:
    st.subheader(f"Seven-day nutrition trend through {selected_date:%B %d}")
    daily_totals = {
        (week_start + timedelta(days=offset)).isoformat(): {
            "calories": 0.0,
            "protein": 0.0,
            "carbs": 0.0,
            "fats": 0.0,
            "fiber": 0.0,
            "sugar": 0.0,
            "sodium_mg": 0.0,
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
            "Fiber (g)": totals["fiber"],
            "Sugar (g)": totals["sugar"],
            "Sodium (mg)": totals["sodium_mg"],
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
    weekly_calories = sum(row["Calories"] for row in trend_rows)
    weekly_remaining = weekly_goal["calorie_goal"] - weekly_calories
    weekly_col, weekly_remaining_col = st.columns(2)
    weekly_col.metric("Seven-day calories", f"{weekly_calories:,.0f} kcal")
    weekly_remaining_col.metric(
        "Weekly calorie budget",
        f"{abs(weekly_remaining):,.0f} kcal {'remaining' if weekly_remaining >= 0 else 'over'}",
    )
    st.progress(
        min(weekly_calories / weekly_goal["calorie_goal"], 1.0),
        text=f"{weekly_calories:,.0f} of {weekly_goal['calorie_goal']:,.0f} kcal budgeted",
    )
    st.bar_chart(trend_rows, x="Date", y="Calories")
    st.dataframe(trend_rows, hide_index=True, use_container_width=True)

    csv_buffer = StringIO()
    csv_writer = csv.DictWriter(
        csv_buffer,
        fieldnames=[
            "Date",
            "Calories",
            "Protein (g)",
            "Carbs (g)",
            "Fat (g)",
            "Fiber (g)",
            "Sugar (g)",
            "Sodium (mg)",
        ],
    )
    csv_writer.writeheader()
    csv_writer.writerows(trend_rows)
    st.download_button(
        "Download seven-day report",
        data=csv_buffer.getvalue(),
        file_name=f"macromind_nutrition_{week_start.isoformat()}_{selected_date.isoformat()}.csv",
        mime="text/csv",
    )
