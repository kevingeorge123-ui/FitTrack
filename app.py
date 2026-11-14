"""FitTrack - a HealthifyMe-style health & nutrition tracker built with Streamlit."""
import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="FitTrack", page_icon="🥗", layout="wide")

DATA_FILE = Path("fittrack_data.json")

# Per serving: kcal, protein g, carbs g, fat g
FOODS = {
    "Roti / Chapati (1 medium)": (104, 3.1, 18.0, 2.5),
    "Steamed rice (1 cup)": (205, 4.3, 45.0, 0.4),
    "Dal / Lentil curry (1 cup)": (180, 12.0, 28.0, 3.0),
    "Paneer (100 g)": (265, 18.0, 3.0, 20.0),
    "Chicken breast, cooked (100 g)": (165, 31.0, 0.0, 3.6),
    "Egg, boiled (1 large)": (78, 6.3, 0.6, 5.3),
    "Idli (1 piece)": (58, 2.0, 12.0, 0.4),
    "Dosa, plain (1 piece)": (133, 3.0, 25.0, 2.5),
    "Poha (1 cup)": (250, 4.5, 45.0, 6.0),
    "Oats, cooked (1 cup)": (166, 5.9, 28.0, 3.6),
    "Banana (1 medium)": (105, 1.3, 27.0, 0.4),
    "Apple (1 medium)": (95, 0.5, 25.0, 0.3),
    "Milk, whole (1 cup)": (149, 8.0, 12.0, 8.0),
    "Curd / Yogurt (1 cup)": (150, 8.5, 11.4, 8.0),
    "Almonds (10 pieces)": (70, 2.6, 2.6, 6.0),
    "Peanut butter (1 tbsp)": (94, 3.6, 3.2, 8.0),
    "Whole wheat bread (1 slice)": (81, 4.0, 13.8, 1.1),
    "Salad, mixed veg (1 bowl)": (50, 2.0, 10.0, 0.3),
    "Samosa (1 piece)": (262, 3.5, 24.0, 17.0),
    "Biryani, chicken (1 cup)": (290, 14.0, 36.0, 9.0),
    "Pizza slice (1 slice)": (285, 12.0, 36.0, 10.0),
    "Burger (1 regular)": (354, 17.0, 29.0, 18.0),
    "French fries (1 medium)": (365, 4.0, 48.0, 17.0),
    "Coffee with milk & sugar (1 cup)": (60, 2.0, 8.0, 2.0),
    "Whey protein shake (1 scoop)": (120, 24.0, 3.0, 1.5),
}

MEALS = ["Breakfast", "Lunch", "Snack", "Dinner"]

WORKOUTS = {
    "Walking (brisk)": 4.3,
    "Running": 9.8,
    "Cycling": 7.5,
    "Swimming": 8.0,
    "Yoga": 3.0,
    "Strength training": 5.0,
    "HIIT": 8.5,
    "Dancing / Zumba": 6.5,
    "Badminton": 5.5,
    "Football": 7.0,
}

ACTIVITY = {
    "Sedentary (little or no exercise)": 1.2,
    "Light (1-3 days/week)": 1.375,
    "Moderate (3-5 days/week)": 1.55,
    "Very active (6-7 days/week)": 1.725,
}

GOALS = {"Lose weight": -500, "Maintain weight": 0, "Gain weight": 400}


def default_state() -> dict:
    return {
        "profile": {
            "name": "",
            "sex": "Male",
            "age": 28,
            "height_cm": 170.0,
            "weight_kg": 70.0,
            "target_weight_kg": 65.0,
            "activity": list(ACTIVITY)[1],
            "goal": "Lose weight",
            "water_goal_ml": 2500,
        },
        "foods": [],
        "water": {},
        "workouts": [],
        "weights": [],
        "custom_foods": {},
    }


def load_data() -> dict:
    state = default_state()
    if DATA_FILE.exists():
        try:
            state.update(json.loads(DATA_FILE.read_text()))
        except (json.JSONDecodeError, OSError):
            pass
    return state


def save_data() -> None:
    try:
        DATA_FILE.write_text(json.dumps(st.session_state.data, indent=2))
    except OSError:
        pass


if "data" not in st.session_state:
    st.session_state.data = load_data()

D = st.session_state.data


def calc_bmr(p: dict) -> float:
    base = 10 * p["weight_kg"] + 6.25 * p["height_cm"] - 5 * p["age"]
    return base + (5 if p["sex"] == "Male" else -161)


def calc_targets(p: dict) -> dict:
    bmr = calc_bmr(p)
    tdee = bmr * ACTIVITY[p["activity"]]
    calories = max(1200, round(tdee + GOALS[p["goal"]]))
    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "calories": calories,
        "protein": round(calories * 0.25 / 4),
        "carbs": round(calories * 0.45 / 4),
        "fat": round(calories * 0.30 / 9),
    }


def calc_bmi(p: dict) -> float:
    h = p["height_cm"] / 100
    return p["weight_kg"] / (h * h)


def bmi_label(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Healthy"
    if bmi < 30:
        return "Overweight"
    return "Obese"


def all_foods() -> dict:
    merged = dict(FOODS)
    merged.update({k: tuple(v) for k, v in D["custom_foods"].items()})
    return merged


def day_foods(day: date) -> pd.DataFrame:
    rows = [f for f in D["foods"] if f["date"] == day.isoformat()]
    return pd.DataFrame(rows)


def day_totals(day: date) -> dict:
    df = day_foods(day)
    if df.empty:
        return {"kcal": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    return {k: float(df[k].sum()) for k in ["kcal", "protein", "carbs", "fat"]}


def day_burned(day: date) -> float:
    return sum(w["kcal"] for w in D["workouts"] if w["date"] == day.isoformat())


st.sidebar.title("🥗 FitTrack")
if D["profile"]["name"]:
    st.sidebar.caption(f"Hi, {D['profile']['name']}!")

page = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Log Food", "Water", "Workouts", "Weight", "Profile", "Backup"],
)
selected_day = st.sidebar.date_input("Date", value=date.today(), max_value=date.today())
targets = calc_targets(D["profile"])


def page_dashboard():
    st.header(f"Dashboard - {selected_day.strftime('%A, %d %b %Y')}")
    totals = day_totals(selected_day)
    burned = day_burned(selected_day)
    net = totals["kcal"] - burned
    remaining = targets["calories"] - net

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Eaten", f"{totals['kcal']:.0f} kcal")
    c2.metric("Burned", f"{burned:.0f} kcal")
    c3.metric("Goal", f"{targets['calories']} kcal")
    c4.metric("Remaining", f"{remaining:.0f} kcal",
              delta="over budget" if remaining < 0 else None, delta_color="inverse")
    st.progress(min(max(net / targets["calories"], 0.0), 1.0), text="Daily calorie budget")

    st.subheader("Macros")
    m1, m2, m3 = st.columns(3)
    for col, key, label in [(m1, "protein", "Protein"), (m2, "carbs", "Carbs"), (m3, "fat", "Fat")]:
        col.metric(label, f"{totals[key]:.0f} g / {targets[key]} g")
        col.progress(min(totals[key] / targets[key], 1.0))

    water = D["water"].get(selected_day.isoformat(), 0)
    st.subheader("Water")
    st.progress(min(water / D["profile"]["water_goal_ml"], 1.0),
                text=f"{water} / {D['profile']['water_goal_ml']} ml")

    st.subheader("Last 7 days - calories eaten")
    days = [selected_day - timedelta(days=i) for i in range(6, -1, -1)]
    chart = pd.DataFrame(
        {"Eaten": [day_totals(d)["kcal"] for d in days]},
        index=[d.strftime("%d %b") for d in days],
    )
    st.bar_chart(chart)
    st.caption(f"Daily goal: {targets['calories']} kcal")

    bmi = calc_bmi(D["profile"])
    st.info(f"BMI: **{bmi:.1f}** ({bmi_label(bmi)}) · BMR: {targets['bmr']} kcal · "
            f"Maintenance: {targets['tdee']} kcal")


def page_food():
    st.header("Log Food")
    foods = all_foods()

    with st.form("food_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([3, 1, 1])
        name = c1.selectbox("Food (type to search)", sorted(foods))
        servings = c2.number_input("Servings", 0.25, 20.0, 1.0, 0.25)
        meal = c3.selectbox("Meal", MEALS)
        if st.form_submit_button("Add to log", type="primary"):
            kcal, p, c, f = foods[name]
            D["foods"].append({
                "date": selected_day.isoformat(), "meal": meal, "name": name,
                "servings": servings, "kcal": round(kcal * servings, 1),
                "protein": round(p * servings, 1), "carbs": round(c * servings, 1),
                "fat": round(f * servings, 1),
            })
            save_data()
            st.success(f"Added {servings} x {name}")

    with st.expander("Add a custom food"):
        with st.form("custom_food", clear_on_submit=True):
            cname = st.text_input("Name (include the serving size)")
            a, b, c_, d = st.columns(4)
            ck = a.number_input("kcal", 0.0, 3000.0, 100.0)
            cp = b.number_input("Protein g", 0.0, 300.0, 0.0)
            cc = c_.number_input("Carbs g", 0.0, 500.0, 0.0)
            cf = d.number_input("Fat g", 0.0, 300.0, 0.0)
            if st.form_submit_button("Save food") and cname.strip():
                D["custom_foods"][cname.strip()] = [ck, cp, cc, cf]
                save_data()
                st.success("Saved. It now appears in the food list.")
                st.rerun()

    st.subheader(f"Today's log ({selected_day.strftime('%d %b')})")
    df = day_foods(selected_day)
    if df.empty:
        st.write("Nothing logged yet.")
        return
    for meal in MEALS:
        sub = df[df["meal"] == meal]
        if sub.empty:
            continue
        st.markdown(f"**{meal}** - {sub['kcal'].sum():.0f} kcal")
        st.dataframe(sub[["name", "servings", "kcal", "protein", "carbs", "fat"]],
                     hide_index=True, use_container_width=True)

    if st.button("Remove last entry for this day"):
        for i in range(len(D["foods"]) - 1, -1, -1):
            if D["foods"][i]["date"] == selected_day.isoformat():
                D["foods"].pop(i)
                break
        save_data()
        st.rerun()


def page_water():
    st.header("Water Tracker")
    key = selected_day.isoformat()
    current = D["water"].get(key, 0)
    goal = D["profile"]["water_goal_ml"]
    st.metric("Today", f"{current} ml", f"goal {goal} ml", delta_color="off")
    st.progress(min(current / goal, 1.0))

    cols = st.columns(4)
    for col, amt in zip(cols, [150, 250, 500, 1000]):
        if col.button(f"+{amt} ml", use_container_width=True):
            D["water"][key] = current + amt
            save_data()
            st.rerun()
    if st.button("Undo / reset today"):
        D["water"][key] = 0
        save_data()
        st.rerun()


def page_workouts():
    st.header("Workouts")
    with st.form("workout_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.selectbox("Activity", list(WORKOUTS))
        minutes = c2.number_input("Minutes", 5, 300, 30, 5)
        if st.form_submit_button("Log workout", type="primary"):
            kcal = WORKOUTS[name] * D["profile"]["weight_kg"] * minutes / 60
            D["workouts"].append({"date": selected_day.isoformat(), "name": name,
                                  "minutes": minutes, "kcal": round(kcal)})
            save_data()
            st.success(f"Logged {name}: about {kcal:.0f} kcal burned")

    rows = [w for w in D["workouts"] if w["date"] == selected_day.isoformat()]
    st.subheader("Today")
    if rows:
        st.dataframe(pd.DataFrame(rows)[["name", "minutes", "kcal"]],
                     hide_index=True, use_container_width=True)
    else:
        st.write("No workouts logged.")

    st.subheader("Last 7 days - calories burned")
    days = [selected_day - timedelta(days=i) for i in range(6, -1, -1)]
    st.bar_chart(pd.DataFrame({"Burned": [day_burned(d) for d in days]},
                              index=[d.strftime("%d %b") for d in days]))


def page_weight():
    st.header("Weight Tracker")
    with st.form("weight_form", clear_on_submit=False):
        w = st.number_input("Weight (kg)", 20.0, 300.0, float(D["profile"]["weight_kg"]), 0.1)
        if st.form_submit_button("Save weight", type="primary"):
            D["weights"] = [x for x in D["weights"] if x["date"] != selected_day.isoformat()]
            D["weights"].append({"date": selected_day.isoformat(), "weight_kg": w})
            D["profile"]["weight_kg"] = w
            save_data()
            st.success("Saved")
            st.rerun()

    if D["weights"]:
        df = pd.DataFrame(D["weights"]).sort_values("date")
        df["date"] = pd.to_datetime(df["date"])
        st.line_chart(df.set_index("date")["weight_kg"])
        start, now = df["weight_kg"].iloc[0], df["weight_kg"].iloc[-1]
        target = D["profile"]["target_weight_kg"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Current", f"{now:.1f} kg", f"{now - start:+.1f} kg since start", delta_color="off")
        c2.metric("Target", f"{target:.1f} kg")
        c3.metric("To go", f"{abs(now - target):.1f} kg")
    else:
        st.write("No weight entries yet.")


def page_profile():
    st.header("Profile & Goals")
    p = D["profile"]
    with st.form("profile_form"):
        p["name"] = st.text_input("Name", p["name"])
        c1, c2, c3 = st.columns(3)
        p["sex"] = c1.selectbox("Sex", ["Male", "Female"], index=0 if p["sex"] == "Male" else 1)
        p["age"] = c2.number_input("Age", 10, 100, int(p["age"]))
        p["height_cm"] = c3.number_input("Height (cm)", 100.0, 250.0, float(p["height_cm"]))
        c4, c5 = st.columns(2)
        p["weight_kg"] = c4.number_input("Weight (kg)", 20.0, 300.0, float(p["weight_kg"]), 0.1)
        p["target_weight_kg"] = c5.number_input("Target weight (kg)", 20.0, 300.0,
                                                float(p["target_weight_kg"]), 0.1)
        p["activity"] = st.selectbox("Activity level", list(ACTIVITY),
                                     index=list(ACTIVITY).index(p["activity"]))
        p["goal"] = st.selectbox("Goal", list(GOALS), index=list(GOALS).index(p["goal"]))
        p["water_goal_ml"] = st.number_input("Water goal (ml)", 500, 8000,
                                             int(p["water_goal_ml"]), 250)
        if st.form_submit_button("Save profile", type="primary"):
            save_data()
            st.success("Profile saved")
            st.rerun()

    t = calc_targets(p)
    st.subheader("Your daily targets")
    a, b, c, d = st.columns(4)
    a.metric("Calories", f"{t['calories']} kcal")
    b.metric("Protein", f"{t['protein']} g")
    c.metric("Carbs", f"{t['carbs']} g")
    d.metric("Fat", f"{t['fat']} g")
    st.caption("Estimated with the Mifflin-St Jeor formula. This is general guidance, "
               "not medical advice.")


def page_backup():
    st.header("Backup & Restore")
    st.write("Hosted apps can lose local files on restart, so download a backup regularly.")
    st.download_button("Download my data (JSON)", json.dumps(D, indent=2),
                       file_name="fittrack_backup.json", mime="application/json")
    up = st.file_uploader("Restore from backup", type="json")
    if up is not None and st.button("Restore now"):
        try:
            restored = default_state()
            restored.update(json.load(up))
            st.session_state.data = restored
            D.clear()
            D.update(restored)
            save_data()
            st.success("Restored")
            st.rerun()
        except (json.JSONDecodeError, ValueError):
            st.error("That file is not a valid backup.")


PAGES = {
    "Dashboard": page_dashboard, "Log Food": page_food, "Water": page_water,
    "Workouts": page_workouts, "Weight": page_weight, "Profile": page_profile,
    "Backup": page_backup,
}
PAGES[page]()
