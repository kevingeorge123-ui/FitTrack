"""FitTrack - a HealthifyMe-style health & nutrition tracker built with Streamlit."""
import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="FitTrack", page_icon="🥗", layout="wide")

DATA_FILE = Path("fittrack_data.json")

# ----------------------------------------------------------------------------
# Style
# ----------------------------------------------------------------------------
CSS = """
<style>
#MainMenu, footer {visibility: hidden;}
.block-container {padding-top: 2rem; max-width: 1100px;}
.hero {
    background: linear-gradient(120deg, #16a34a 0%, #0ea5a4 100%);
    color: #fff; padding: 22px 26px; border-radius: 18px; margin-bottom: 18px;
    box-shadow: 0 6px 18px rgba(22,163,74,.25);
}
.hero h2 {margin: 0; font-size: 1.6rem; color: #fff;}
.hero p {margin: 4px 0 0 0; opacity: .92;}
.stat {
    background: rgba(22,163,74,.08); border: 1px solid rgba(22,163,74,.25);
    border-radius: 14px; padding: 14px 16px; text-align: center;
}
.stat span {display: block; font-size: .8rem; opacity: .75; text-transform: uppercase; letter-spacing: .04em;}
.stat b {display: block; font-size: 1.6rem; margin-top: 2px;}
.stat small {opacity: .7;}
.ring-wrap {position: relative; width: 190px; height: 190px; margin: 6px auto 14px auto;}
.ring {
    width: 100%; height: 100%; border-radius: 50%;
    background: conic-gradient(var(--c) calc(var(--pct) * 1%), rgba(128,128,128,.22) 0);
    -webkit-mask: radial-gradient(farthest-side, transparent 72%, #000 73%);
            mask: radial-gradient(farthest-side, transparent 72%, #000 73%);
}
.ring-text {
    position: absolute; inset: 0; display: flex; flex-direction: column;
    align-items: center; justify-content: center; text-align: center;
}
.ring-text b {font-size: 2rem; line-height: 1.1;}
.ring-text span {font-size: .8rem; opacity: .7;}
.bar-row {margin: 10px 0;}
.bar-label {display: flex; justify-content: space-between; font-size: .9rem; margin-bottom: 4px;}
.bar-track {background: rgba(128,128,128,.22); border-radius: 99px; height: 10px; overflow: hidden;}
.bar-fill {height: 100%; border-radius: 99px;}
.preview {
    background: rgba(14,165,164,.10); border: 1px dashed rgba(14,165,164,.5);
    border-radius: 12px; padding: 12px 16px; margin: 8px 0 14px 0;
}
.meal-title {font-weight: 700; margin-top: 14px;}
div.stButton > button[kind="primary"] {
    background: linear-gradient(120deg, #16a34a, #0ea5a4); border: 0; color: #fff;
    border-radius: 10px; font-weight: 600;
}
section[data-testid="stSidebar"] {border-right: 1px solid rgba(128,128,128,.2);}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Reference data
# Per serving: (serving size in grams, kcal, protein g, carbs g, fat g)
# ----------------------------------------------------------------------------
FOODS_PER_SERVING = {
    "Roti / Chapati (1 medium)": (40, 104, 3.1, 18.0, 2.5),
    "Steamed rice (1 cup)": (158, 205, 4.3, 45.0, 0.4),
    "Dal / Lentil curry (1 cup)": (240, 180, 12.0, 28.0, 3.0),
    "Paneer (100 g)": (100, 265, 18.0, 3.0, 20.0),
    "Chicken breast, cooked (100 g)": (100, 165, 31.0, 0.0, 3.6),
    "Egg, boiled (1 large)": (50, 78, 6.3, 0.6, 5.3),
    "Idli (1 piece)": (40, 58, 2.0, 12.0, 0.4),
    "Dosa, plain (1 piece)": (50, 133, 3.0, 25.0, 2.5),
    "Poha (1 cup)": (150, 250, 4.5, 45.0, 6.0),
    "Oats, cooked (1 cup)": (234, 166, 5.9, 28.0, 3.6),
    "Banana (1 medium)": (118, 105, 1.3, 27.0, 0.4),
    "Apple (1 medium)": (182, 95, 0.5, 25.0, 0.3),
    "Milk, whole (1 cup)": (244, 149, 8.0, 12.0, 8.0),
    "Curd / Yogurt (1 cup)": (245, 150, 8.5, 11.4, 8.0),
    "Almonds (10 pieces)": (12, 70, 2.6, 2.6, 6.0),
    "Peanut butter (1 tbsp)": (16, 94, 3.6, 3.2, 8.0),
    "Whole wheat bread (1 slice)": (30, 81, 4.0, 13.8, 1.1),
    "Salad, mixed veg (1 bowl)": (150, 50, 2.0, 10.0, 0.3),
    "Samosa (1 piece)": (50, 262, 3.5, 24.0, 17.0),
    "Biryani, chicken (1 cup)": (200, 290, 14.0, 36.0, 9.0),
    "Pizza slice (1 slice)": (107, 285, 12.0, 36.0, 10.0),
    "Burger (1 regular)": (150, 354, 17.0, 29.0, 18.0),
    "French fries (1 medium)": (117, 365, 4.0, 48.0, 17.0),
    "Coffee with milk & sugar (1 cup)": (240, 60, 2.0, 8.0, 2.0),
    "Whey protein shake (1 scoop)": (30, 120, 24.0, 3.0, 1.5),
}

# name -> {"serving_g": grams in one serving, "per100": [kcal, protein, carbs, fat] per 100 g}
FOODS = {
    name: {"serving_g": v[0], "per100": [x / v[0] * 100 for x in v[1:]]}
    for name, v in FOODS_PER_SERVING.items()
}

# Units for the amount box. Value = grams in one unit (None = use the food's serving size).
# ml and l assume 1 ml = 1 g (close enough for water, milk, tea, coffee).
UNITS = {
    "Serving": None,
    "Gram (g)": 1.0,
    "Milligram (mg)": 0.001,
    "Kilogram (kg)": 1000.0,
    "Ounce (oz)": 28.3495,
    "Pound (lb)": 453.592,
    "Millilitre (ml)": 1.0,
    "Litre (l)": 1000.0,
}
UNIT_DEFAULT = {"Serving": 1.0, "Gram (g)": 100.0, "Milligram (mg)": 500.0,
                "Kilogram (kg)": 0.1, "Ounce (oz)": 3.5, "Pound (lb)": 0.25,
                "Millilitre (ml)": 250.0, "Litre (l)": 0.25}
UNIT_STEP = {"Serving": 0.25, "Gram (g)": 10.0, "Milligram (mg)": 100.0,
             "Kilogram (kg)": 0.05, "Ounce (oz)": 0.5, "Pound (lb)": 0.05,
             "Millilitre (ml)": 10.0, "Litre (l)": 0.05}

MEALS = {"Breakfast": "🌅", "Lunch": "🍛", "Snack": "🍎", "Dinner": "🌙"}

# MET values for common workouts
WORKOUTS = {
    "Walking (brisk)": 4.3, "Running": 9.8, "Cycling": 7.5, "Swimming": 8.0,
    "Yoga": 3.0, "Strength training": 5.0, "HIIT": 8.5,
    "Dancing / Zumba": 6.5, "Badminton": 5.5, "Football": 7.0,
}

ACTIVITY = {
    "Sedentary (little or no exercise)": 1.2,
    "Light (1-3 days/week)": 1.375,
    "Moderate (3-5 days/week)": 1.55,
    "Very active (6-7 days/week)": 1.725,
}

GOALS = {"Lose weight": -500, "Maintain weight": 0, "Gain weight": 400}


def to_grams(amount: float, unit: str, serving_g: float) -> float:
    factor = UNITS[unit]
    return amount * serving_g if factor is None else amount * factor


def nutrition_for(food: dict, grams: float) -> dict:
    k, p, c, f = food["per100"]
    r = grams / 100.0
    return {"kcal": round(k * r, 1), "protein": round(p * r, 1),
            "carbs": round(c * r, 1), "fat": round(f * r, 1)}


# ----------------------------------------------------------------------------
# Persistence
# ----------------------------------------------------------------------------
def default_state() -> dict:
    return {
        "profile": {
            "name": "", "sex": "Male", "age": 28, "height_cm": 170.0,
            "weight_kg": 70.0, "target_weight_kg": 65.0,
            "activity": list(ACTIVITY)[1], "goal": "Lose weight",
            "water_goal_ml": 2500,
        },
        "foods": [],         # logged food entries
        "water": {},         # {date_iso: ml}
        "workouts": [],      # {date, name, minutes, kcal}
        "weights": [],       # {date, weight_kg}
        "custom_foods": {},  # name -> {"serving_g", "per100"}
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
        pass  # read-only hosting: use the Backup page instead


if "data" not in st.session_state:
    st.session_state.data = load_data()

D = st.session_state.data


# ----------------------------------------------------------------------------
# Calculations
# ----------------------------------------------------------------------------
def calc_bmr(p: dict) -> float:
    """Mifflin-St Jeor equation."""
    base = 10 * p["weight_kg"] + 6.25 * p["height_cm"] - 5 * p["age"]
    return base + (5 if p["sex"] == "Male" else -161)


def calc_targets(p: dict) -> dict:
    bmr = calc_bmr(p)
    tdee = bmr * ACTIVITY[p["activity"]]
    calories = max(1200, round(tdee + GOALS[p["goal"]]))
    return {
        "bmr": round(bmr), "tdee": round(tdee), "calories": calories,
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
    for name, v in D["custom_foods"].items():
        if isinstance(v, dict):
            merged[name] = v
        else:  # old format: [kcal, protein, carbs, fat] per serving
            merged[name] = {"serving_g": 100, "per100": list(v)}
    return merged


def food_rows(day: date) -> list:
    """List of (index in D['foods'], entry) for a day."""
    return [(i, f) for i, f in enumerate(D["foods"]) if f["date"] == day.isoformat()]


def day_totals(day: date) -> dict:
    totals = {"kcal": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    for _, f in food_rows(day):
        for k in totals:
            totals[k] += float(f.get(k, 0))
    return totals


def day_burned(day: date) -> float:
    return sum(w["kcal"] for w in D["workouts"] if w["date"] == day.isoformat())


def entry_amount(f: dict) -> str:
    return f.get("amount_text") or f"{f.get('servings', 1)} serving"


# ----------------------------------------------------------------------------
# UI helpers
# ----------------------------------------------------------------------------
def stat_card(label: str, value: str, sub: str = "") -> str:
    small = f"<small>{sub}</small>" if sub else ""
    return f'<div class="stat"><span>{label}</span><b>{value}</b>{small}</div>'


def bar(label: str, value: float, target: float, color: str, unit: str = "g") -> str:
    pct = 0 if target <= 0 else min(value / target * 100, 100)
    return (f'<div class="bar-row"><div class="bar-label"><span>{label}</span>'
            f'<span>{value:.0f} / {target:.0f} {unit}</span></div>'
            f'<div class="bar-track"><div class="bar-fill" '
            f'style="width:{pct:.0f}%;background:{color}"></div></div></div>')


def hero(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="hero"><h2>{title}</h2><p>{subtitle}</p></div>',
                unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
st.sidebar.markdown("## 🥗 FitTrack")
if D["profile"]["name"]:
    st.sidebar.caption(f"Hi, {D['profile']['name']}!")

PAGE_NAMES = ["🏠 Dashboard", "🍽️ Log Food", "💧 Water", "🏃 Workouts",
              "⚖️ Weight", "👤 Profile", "💾 Backup"]
page = st.sidebar.radio("Menu", PAGE_NAMES, label_visibility="collapsed")
selected_day = st.sidebar.date_input("Date", value=date.today(), max_value=date.today())
targets = calc_targets(D["profile"])


# ----------------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------------
def page_dashboard():
    name = D["profile"]["name"]
    hero(f"Hello{', ' + name if name else ''}! 👋",
         selected_day.strftime("%A, %d %B %Y") + " · Here is your day at a glance")

    totals = day_totals(selected_day)
    burned = day_burned(selected_day)
    net = totals["kcal"] - burned
    goal = targets["calories"]
    remaining = goal - net
    pct = min(max(net / goal * 100, 0), 100)
    color = "#dc2626" if remaining < 0 else "#16a34a"

    left, right = st.columns([1, 1.4])
    with left:
        label = "kcal over" if remaining < 0 else "kcal left"
        st.markdown(
            f'<div class="ring-wrap"><div class="ring" style="--pct:{pct:.0f};--c:{color}"></div>'
            f'<div class="ring-text"><b>{abs(remaining):.0f}</b><span>{label}</span></div></div>',
            unsafe_allow_html=True)
        a, b, c = st.columns(3)
        a.markdown(stat_card("Eaten", f"{totals['kcal']:.0f}"), unsafe_allow_html=True)
        b.markdown(stat_card("Burned", f"{burned:.0f}"), unsafe_allow_html=True)
        c.markdown(stat_card("Goal", f"{goal}"), unsafe_allow_html=True)
    with right:
        st.markdown("#### Macros")
        st.markdown(
            bar("Protein", totals["protein"], targets["protein"], "#3b82f6")
            + bar("Carbs", totals["carbs"], targets["carbs"], "#f59e0b")
            + bar("Fat", totals["fat"], targets["fat"], "#ec4899"),
            unsafe_allow_html=True)
        water = D["water"].get(selected_day.isoformat(), 0)
        st.markdown("#### Water")
        st.markdown(bar("Today", water, D["profile"]["water_goal_ml"], "#0ea5e9", "ml"),
                    unsafe_allow_html=True)

    st.markdown("#### Last 7 days - calories eaten")
    days = [selected_day - timedelta(days=i) for i in range(6, -1, -1)]
    chart = pd.DataFrame({"Eaten (kcal)": [day_totals(d)["kcal"] for d in days]},
                         index=[d.strftime("%d %b") for d in days])
    st.bar_chart(chart, color="#16a34a")
    st.caption(f"Daily goal: {goal} kcal")

    bmi = calc_bmi(D["profile"])
    x, y, z = st.columns(3)
    x.markdown(stat_card("BMI", f"{bmi:.1f}", bmi_label(bmi)), unsafe_allow_html=True)
    y.markdown(stat_card("BMR", f"{targets['bmr']}", "kcal at rest"), unsafe_allow_html=True)
    z.markdown(stat_card("Maintenance", f"{targets['tdee']}", "kcal / day"),
               unsafe_allow_html=True)


def page_food():
    hero("Log Food 🍽️", "Pick a food, choose a unit (serving, g, mg, kg...) and add it")
    foods = all_foods()

    c1, c2, c3 = st.columns([3, 2, 2])
    name = c1.selectbox("Food (type to search)", sorted(foods))
    unit = c2.selectbox("Unit", list(UNITS))
    meal = c3.selectbox("Meal", list(MEALS), format_func=lambda m: f"{MEALS[m]} {m}")

    food = foods[name]
    amount = st.number_input(
        f"Amount ({unit})", min_value=0.001, value=UNIT_DEFAULT[unit],
        step=UNIT_STEP[unit], format="%.2f", key=f"amt_{name}_{unit}")

    grams = to_grams(amount, unit, food["serving_g"])
    n = nutrition_for(food, grams)
    st.markdown(
        f'<div class="preview"><b>{amount:g} {unit}</b> of {name} = <b>{grams:,.1f} g</b><br>'
        f'🔥 <b>{n["kcal"]:.0f}</b> kcal &nbsp;·&nbsp; 🥩 Protein <b>{n["protein"]:.1f}</b> g '
        f'&nbsp;·&nbsp; 🍞 Carbs <b>{n["carbs"]:.1f}</b> g &nbsp;·&nbsp; 🧈 Fat <b>{n["fat"]:.1f}</b> g'
        f'<br><small>1 serving = {food["serving_g"]:g} g</small></div>',
        unsafe_allow_html=True)

    if st.button("➕ Add to log", type="primary"):
        D["foods"].append({
            "date": selected_day.isoformat(), "meal": meal, "name": name,
            "amount_text": f"{amount:g} {unit.split(' (')[0].lower()}",
            "grams": round(grams, 1), **n,
        })
        save_data()
        st.success(f"Added {amount:g} {unit} of {name} to {meal}")
        st.rerun()

    with st.expander("➕ Add a custom food"):
        with st.form("custom_food", clear_on_submit=True):
            cname = st.text_input("Food name")
            serving_g = st.number_input("1 serving weighs (g)", 1.0, 5000.0, 100.0)
            st.caption("Enter the nutrition values per 100 g (from the food label).")
            a, b, c_, d = st.columns(4)
            ck = a.number_input("kcal / 100 g", 0.0, 1000.0, 100.0)
            cp = b.number_input("Protein g", 0.0, 100.0, 0.0)
            cc = c_.number_input("Carbs g", 0.0, 100.0, 0.0)
            cf = d.number_input("Fat g", 0.0, 100.0, 0.0)
            if st.form_submit_button("Save food") and cname.strip():
                D["custom_foods"][cname.strip()] = {
                    "serving_g": serving_g, "per100": [ck, cp, cc, cf]}
                save_data()
                st.success("Saved. It now appears in the food list.")
                st.rerun()

    st.markdown(f"### Log for {selected_day.strftime('%d %b %Y')}")
    rows = food_rows(selected_day)
    if not rows:
        st.info("Nothing logged yet.")
        return
    for meal_name, icon in MEALS.items():
        items = [(i, f) for i, f in rows if f["meal"] == meal_name]
        if not items:
            continue
        total = sum(f["kcal"] for _, f in items)
        st.markdown(f'<div class="meal-title">{icon} {meal_name} · {total:.0f} kcal</div>',
                    unsafe_allow_html=True)
        st.dataframe(
            pd.DataFrame([{"Food": f["name"], "Amount": entry_amount(f), "kcal": f["kcal"],
                           "Protein": f["protein"], "Carbs": f["carbs"], "Fat": f["fat"]}
                          for _, f in items]),
            hide_index=True)

    options = {f"{f['meal']} - {f['name']} ({entry_amount(f)})": i for i, f in rows}
    to_remove = st.selectbox("Remove an entry", ["-"] + list(options))
    if to_remove != "-" and st.button("🗑️ Remove selected"):
        D["foods"].pop(options[to_remove])
        save_data()
        st.rerun()


def page_water():
    hero("Water Tracker 💧", "Stay hydrated - tap to add what you drink")
    key = selected_day.isoformat()
    current = D["water"].get(key, 0)
    goal = D["profile"]["water_goal_ml"]
    st.markdown(bar("Today", current, goal, "#0ea5e9", "ml"), unsafe_allow_html=True)

    cols = st.columns(4)
    for col, amt in zip(cols, [150, 250, 500, 1000]):
        if col.button(f"💧 +{amt} ml", key=f"w{amt}"):
            D["water"][key] = current + amt
            save_data()
            st.rerun()
    if st.button("Reset today"):
        D["water"][key] = 0
        save_data()
        st.rerun()


def page_workouts():
    hero("Workouts 🏃", "Log activity and see the calories you burn")
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
    st.markdown("#### Today")
    if rows:
        st.dataframe(pd.DataFrame(rows)[["name", "minutes", "kcal"]], hide_index=True)
    else:
        st.info("No workouts logged.")

    st.markdown("#### Last 7 days - calories burned")
    days = [selected_day - timedelta(days=i) for i in range(6, -1, -1)]
    st.bar_chart(pd.DataFrame({"Burned (kcal)": [day_burned(d) for d in days]},
                              index=[d.strftime("%d %b") for d in days]),
                 color="#f59e0b")


def page_weight():
    hero("Weight Tracker ⚖️", "Track your progress toward your target")
    with st.form("weight_form"):
        w = st.number_input("Weight (kg)", 20.0, 300.0, float(D["profile"]["weight_kg"]), 0.1)
        if st.form_submit_button("Save weight", type="primary"):
            D["weights"] = [x for x in D["weights"] if x["date"] != selected_day.isoformat()]
            D["weights"].append({"date": selected_day.isoformat(), "weight_kg": w})
            D["profile"]["weight_kg"] = w
            save_data()
            st.rerun()

    if D["weights"]:
        df = pd.DataFrame(D["weights"]).sort_values("date")
        df["date"] = pd.to_datetime(df["date"])
        st.line_chart(df.set_index("date")["weight_kg"], color="#16a34a")
        start, now = df["weight_kg"].iloc[0], df["weight_kg"].iloc[-1]
        target = D["profile"]["target_weight_kg"]
        a, b, c = st.columns(3)
        a.markdown(stat_card("Current", f"{now:.1f} kg", f"{now - start:+.1f} kg since start"),
                   unsafe_allow_html=True)
        b.markdown(stat_card("Target", f"{target:.1f} kg"), unsafe_allow_html=True)
        c.markdown(stat_card("To go", f"{abs(now - target):.1f} kg"), unsafe_allow_html=True)
    else:
        st.info("No weight entries yet.")


def page_profile():
    hero("Profile & Goals 👤", "Your details set your daily calorie and macro targets")
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
            st.rerun()

    t = calc_targets(p)
    st.markdown("#### Your daily targets")
    a, b, c, d = st.columns(4)
    a.markdown(stat_card("Calories", f"{t['calories']}", "kcal"), unsafe_allow_html=True)
    b.markdown(stat_card("Protein", f"{t['protein']}", "g"), unsafe_allow_html=True)
    c.markdown(stat_card("Carbs", f"{t['carbs']}", "g"), unsafe_allow_html=True)
    d.markdown(stat_card("Fat", f"{t['fat']}", "g"), unsafe_allow_html=True)
    st.caption("Estimated with the Mifflin-St Jeor formula. This is general guidance, "
               "not medical advice.")


def page_backup():
    hero("Backup & Restore 💾", "Hosted apps can lose data on restart - download a backup often")
    st.download_button("⬇️ Download my data (JSON)", json.dumps(D, indent=2),
                       file_name="fittrack_backup.json", mime="application/json")
    up = st.file_uploader("Restore from backup", type="json")
    if up is not None and st.button("Restore now"):
        try:
            loaded = json.load(up)
            if not isinstance(loaded, dict):
                raise ValueError("not a backup")
            restored = default_state()
            restored.update(loaded)
            st.session_state.data = restored
            save_data()
            st.rerun()
        except (json.JSONDecodeError, ValueError):
            st.error("That file is not a valid backup.")


PAGES = {
    "🏠 Dashboard": page_dashboard, "🍽️ Log Food": page_food, "💧 Water": page_water,
    "🏃 Workouts": page_workouts, "⚖️ Weight": page_weight, "👤 Profile": page_profile,
    "💾 Backup": page_backup,
}
PAGES[page]()
