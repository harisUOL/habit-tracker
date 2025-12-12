# =========================
# Imports & Constants
# =========================
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

DB_PATH = "db/habits.db"
DATA_PATH = "data/habits.csv"
POINTS_PER_HABIT = 10


# =========================
# Data Utility Functions
# =========================
@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM habits", conn)
    conn.close()

    df["date"] = pd.to_datetime(df["date"])
    return df


def save_completion(date, habit_name, completed):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE habits
        SET completed = ?
        WHERE date = ? AND habit_name = ?
        """,
        (completed, date, habit_name)
    )

    conn.commit()
    conn.close()


def save_data(df: pd.DataFrame):
    df.to_csv(DATA_PATH, index=False)


def calculate_streak(df: pd.DataFrame, habit: str) -> int:
    habit_df = (
        df[df["habit_name"] == habit]
        .sort_values("date")
    )

    streak = 0
    for completed in reversed(habit_df["completed"].tolist()):
        if completed == 1:
            streak += 1
        else:
            break
    return streak


# =========================
# Page Configuration
# =========================
st.set_page_config(
    page_title="Habit Tracker Dashboard",
    layout="wide"
)

st.markdown("## 🎯 Habit Tracker Dashboard")
st.caption("Turn your daily routine into data and progress into a game")
st.divider()


# =========================
# Load Data
# =========================
df = load_data()


# =========================
# Sidebar Filters
# =========================
st.sidebar.header("📅 Filters")

selected_date = st.sidebar.date_input(
    "Select date",
    df["date"].min()
)

selected_date = pd.to_datetime(selected_date)


# =========================
# Filtered Daily Data
# =========================
daily_df = df[df["date"] == selected_date]

if not daily_df.empty:
    daily_completion_pct = daily_df["completed"].mean() * 100
    daily_points = daily_df["completed"].sum() * POINTS_PER_HABIT
else:
    daily_completion_pct = 0
    daily_points = 0


# =========================
# Tabs Layout
# =========================
tab_daily, tab_weekly, tab_monthly = st.tabs(
    ["📅 Daily", "📈 Weekly", "📆 Monthly"]
)


# =========================
# DAILY TAB
# =========================
with tab_daily:

    # --- Metrics ---
    kpi1, kpi2, kpi3 = st.columns(3)

    kpi1.metric("📊 Completion", f"{daily_completion_pct:.0f}%")
    kpi2.metric("🏆 Daily Points", daily_points)
    kpi3.metric("🔥 Active Habits", int(daily_df["completed"].sum()))

    # --- Daily Habits ---
    with st.container():
        st.markdown("### ✅ Daily Habits")

        updated = False

        for idx, row in daily_df.iterrows():
            left, right = st.columns([3, 1])

            with left:
                new_value = st.checkbox(
                    row["habit_name"],
                    value=bool(row["completed"]),
                    key=f"{row['habit_name']}_{selected_date}"
                )

            with right:
                streak = calculate_streak(df, row["habit_name"])
                st.markdown(f"🔥 **{streak}d**")

            if new_value != bool(row["completed"]):
                save_completion(
                    selected_date.strftime("%Y-%m-%d"),
                    row["habit_name"],
                    int(new_value)
                )
                st.cache_data.clear()
                updated = True

        if updated:
            st.success("Habits updated")


    # --- Progress Ring ---
    fig_progress = px.pie(
        values=[daily_completion_pct, 100 - daily_completion_pct],
        names=["Completed", "Missed"],
        hole=0.7,
        title="Daily Progress"
    )
    st.plotly_chart(fig_progress, use_container_width=True)


# =========================
# WEEKLY TAB
# =========================
with tab_weekly:

    weekly = (
        df
        .assign(
            year=df["date"].dt.year,
            week=df["date"].dt.isocalendar().week
        )
        .groupby(["year", "week"], as_index=False)["completed"]
        .mean()
    )

    weekly["completion_pct"] = weekly["completed"] * 100
    weekly["year_week"] = weekly["year"].astype(str) + "-W" + weekly["week"].astype(str)

    fig_weekly = px.line(
        weekly,
        x="year_week",
        y="completion_pct",
        markers=True,
        range_y=[0, 100],
        title="Weekly Completion Trend"
    )

    st.plotly_chart(fig_weekly, use_container_width=True)


# =========================
# MONTHLY TAB (Placeholder)
# =========================
with tab_monthly:

    monthly = (
        df
        .assign(
            year=df["date"].dt.year,
            month=df["date"].dt.month
        )
        .groupby(["year", "month"], as_index=False)["completed"]
        .mean()
    )

    monthly["completion_pct"] = monthly["completed"] * 100

    # Create readable label (e.g. 2025-Jan)
    monthly["year_month"] = (
        monthly["year"].astype(str)
        + "-"
        + monthly["month"].map({
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
            5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
            9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
        })
    )

    st.subheader("📆 Monthly Completion Trend")

    fig_monthly = px.line(
        monthly,
        x="year_month",
        y="completion_pct",
        markers=True,
        range_y=[0, 100],
        title="Monthly Habit Completion"
    )

    avg_monthly = monthly["completion_pct"].mean()

    st.metric(
        "📊 Average Monthly Completion",
        f"{avg_monthly:.1f}%"
    )

    st.caption("📌 Monthly view aggregates all available data across the selected month")

    st.write(monthly)

    st.plotly_chart(fig_monthly, use_container_width=True)


# =========================
# Habit-wise Performance (Global)
# =========================
st.subheader("📊 Habit-wise Completion")

habit_progress = (
    df.groupby("habit_name")["completed"]
      .mean()
      .reset_index()
)

habit_progress["completion_pct"] = habit_progress["completed"] * 100

fig_habits = px.bar(
    habit_progress,
    x="completion_pct",
    y="habit_name",
    orientation="h",
    range_x=[0, 100],
    title="Habit-wise Completion (%)"
)

st.plotly_chart(fig_habits, use_container_width=True)


# =========================
# Debug / Raw Data (Optional)
# =========================
with st.expander("🔍 View Raw Habit Data"):
    st.dataframe(df, use_container_width=True)
