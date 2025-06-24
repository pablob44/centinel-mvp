import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Load data
df = pd.read_csv("fake_transactions.csv")
df["Date"] = pd.to_datetime(df["Date"])
user_df = pd.read_csv("centinel_user_data.csv")
modules_df = pd.read_csv("modules.csv")

# Behavior trigger logic
def derive_behavior_triggers(transactions):
    triggers = set()
    if transactions[transactions["Category"] == "Dining Out"]["Amount"].sum() < -150:
        triggers.add("high_spending")
    if transactions[transactions["Category"] == "Savings"]["Amount"].sum() < 20:
        triggers.add("low_savings")
    if "Crypto Wallet" in transactions["Merchant"].values:
        triggers.add("crypto_interest")
    if len(transactions[transactions["Category"] == "Transport"]) > 5:
        triggers.add("frequent_withdrawals")
    if "Budgeting 101" not in modules_df["title"].values:
        triggers.add("no_budgeting_history")
    if "Index ETF" in transactions["Merchant"].values:
        triggers.add("new_investment_activity")
    return triggers

# Module match scoring
def score_module(row, user_goals, user_triggers):
    module_goals = row["goal_tags"].split(";")
    module_triggers = row["behavior_triggers"].split(";")
    goal_match = len(set(module_goals) & set(user_goals))
    trigger_match = len(set(module_triggers) & set(user_triggers))
    return goal_match + trigger_match

# User & triggers
user = user_df.iloc[0]
user_goals = user["goal_tags"].split(";")
triggers = derive_behavior_triggers(df)

# Layout
st.set_page_config(page_title="Centinel - Analytics", layout="wide")
st.title("📊 Centinel Analytics Dashboard")

# Sidebar (developer reference)
st.sidebar.title("Centinel MVP")
st.sidebar.subheader(f"Welcome back, {user['name']}")
st.sidebar.markdown(f"**Level:** {user['level'].capitalize()}")
st.sidebar.markdown(f"**XP:** {user['xp_points']}")
st.sidebar.markdown(f"**Streak:** {user['streak_days']} days")
st.sidebar.markdown("---")
st.sidebar.markdown("### 🧠 Behavior Triggers (Dev Only)")
st.sidebar.write(", ".join(triggers) if triggers else "None")

# Section 1: Spending Snapshot (7 days)
st.subheader("💸 Spending Snapshot (Last 7 Days)")
last_week = df[df["Date"] >= pd.Timestamp.now() - pd.Timedelta(days=7)]
weekly_total = last_week["Amount"].sum()
top_cats = last_week.groupby("Category")["Amount"].sum().sort_values().head(3)

col1, col2 = st.columns(2)
col1.metric("Total Spent", f"€{-weekly_total:.2f}")
col2.metric("Top Category", top_cats.idxmin() if not top_cats.empty else "N/A")

# Section 2: Category Breakdown (last 3 months)
st.subheader("📊 Spending by Category (3 Months)")
spending_df = df[df["Amount"] < 0]
cat_totals = spending_df.groupby("Category")["Amount"].sum().reset_index()
fig_pie = px.pie(cat_totals, names="Category", values="Amount")
st.plotly_chart(fig_pie, use_container_width=True)

# Section 3: Last Week Tracker (Line)
st.subheader("📈 Daily Spending – Last 7 Days")
last_week_sum = last_week.groupby(last_week["Date"].dt.date)["Amount"].sum().reset_index()
fig_line = px.line(last_week_sum, x="Date", y="Amount", markers=True)
st.plotly_chart(fig_line, use_container_width=True)

# Section 4: Month-over-Month Comparison
st.subheader("📉 Monthly Comparison – Spending Change")
df["Month"] = df["Date"].dt.to_period("M")
monthly_totals = df[df["Amount"] < 0].groupby("Month")["Amount"].sum().reset_index()
monthly_totals["Month"] = monthly_totals["Month"].astype(str)

if len(monthly_totals) >= 2:
    last = monthly_totals.iloc[-1]["Amount"]
    prev = monthly_totals.iloc[-2]["Amount"]
    change = (last - prev) / abs(prev) * 100 if prev != 0 else 0
    col3, col4 = st.columns(2)
    col3.metric("This Month", f"€{-last:.2f}")
    col4.metric("Change from Last Month", f"{change:+.1f}%")

fig_month = px.bar(monthly_totals, x="Month", y="Amount", title="Total Monthly Spending")
st.plotly_chart(fig_month, use_container_width=True)

# Section 5: Investment Trend Line
st.subheader("📈 Investment Activity Over Time")
invest_df = df[df]()_

