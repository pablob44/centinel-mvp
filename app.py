import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Load data
df = pd.read_csv("fake_transactions.csv")
df["Date"] = pd.to_datetime(df["Date"])
user_df = pd.read_csv("centinel_user_data.csv")
modules_df = pd.read_csv("modules.csv")
df_lists = pd.read_csv("centinel_goals_triggers_advice.csv")

# Trigger-to-advice mapping (cleaned)
trigger_to_advice = {
    "high_spending": [
        "Try limiting non-essential categories for a week.",
        "High daily spending? Consider batching purchases weekly."
    ],
    "low_savings": [
        "Boost your savings — even small, regular transfers add up over time.",
        "Low savings detected — explore emergency fund strategies."
    ],
    "crypto_interest": [
        "Crypto detected — great! Just be sure it fits your long-term goals."
    ],
    "frequent_withdrawals": [
        "Frequent withdrawals may indicate poor planning — try using a budget envelope method."
    ],
    "no_budgeting_history": [
        "No budgeting history — start simple with a 50/30/20 plan."
    ],
    "new_investment_activity": [
        "You're actively investing — consider reviewing your diversification."
    ],
    "unstable_income": [
        "Your income seems inconsistent. Consider building a buffer or using income smoothing techniques."
    ],
    "subscription_overlap": [
        "You have multiple subscriptions at once. Consider cancelling one unused service this month."
    ]
}

# Behavioral trigger logic
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

    # New trigger 1: Unstable income
    salary_months = transactions[transactions["Category"] == "Salary"]["Date"].dt.to_period("M").nunique()
    if salary_months < 2:
        triggers.add("unstable_income")

    # New trigger 2: Subscription overlap
    subs = transactions[transactions["Category"] == "Subscriptions"].copy()
    subs["Week"] = subs["Date"].dt.to_period("W")
    if subs.groupby("Week")["Merchant"].nunique().max() >= 2:
        triggers.add("subscription_overlap")

    return triggers

# Module scoring
def score_module(row, user_goals, user_triggers):
    module_goals = row["goal_tags"].split(";")
    module_triggers = row["behavior_triggers"].split(";")
    goal_match = len(set(module_goals) & set(user_goals))
    trigger_match = len(set(module_triggers) & set(user_triggers))
    return goal_match + trigger_match

# Load user and triggers
user = user_df.iloc[0]
user_goals = user["goal_tags"].split(";")
triggers = derive_behavior_triggers(df)

# Streamlit layout
st.set_page_config(page_title="Centinel - Analytics", layout="wide")
st.title("Centinel Analytics Dashboard")

# Sidebar
st.sidebar.title("Centinel MVP")
st.sidebar.subheader(f"Welcome back, {user['name']}")
st.sidebar.markdown(f"Level: {user['level'].capitalize()}")
st.sidebar.markdown(f"XP: {user['xp_points']}")
st.sidebar.markdown(f"Streak: {user['streak_days']} days")
st.sidebar.markdown("---")
st.sidebar.markdown("Behavior Triggers (Dev Only)")
st.sidebar.write(", ".join(triggers) if triggers else "None")

# Weekly overview
recent_spending = df[df["Amount"] < 0].sort_values("Date", ascending=False)
latest_date = recent_spending["Date"].max() if not recent_spending.empty else pd.Timestamp.now()
last_week = df[(df["Date"] >= latest_date - timedelta(days=6)) & 
               (df["Date"] <= latest_date)]

weekly_total = last_week["Amount"].sum() if not last_week.empty else 0
top_cats = last_week.groupby("Category")["Amount"].sum().sort_values().head(3) if not last_week.empty else pd.Series()
col1, col2 = st.columns(2)
col1.metric("Total Spent", f"€{abs(weekly_total):.2f}")
col2.metric("Top Category", top_cats.idxmin() if not top_cats.empty else "N/A")

# Spending Pie Chart
st.subheader("Spending Breakdown (Pie Chart)")
spend_pie = df[~df["Category"].isin(["Salary", "Savings", "Investments"])]
cat_totals = spend_pie.groupby("Category")["Amount"].sum().abs().reset_index()
if not cat_totals.empty:
    fig_pie = px.pie(cat_totals, names="Category", values="Amount")
    st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.info("No spending data available.")

# Daily spending line chart
st.subheader("Daily Spending – Last 7 Days")
exclude = ["Salary", "Savings", "Investments"]
spending_days = last_week[~last_week["Category"].isin(exclude)]
spending_days = spending_days[spending_days["Amount"] < 0]
daily_spend = spending_days.groupby(spending_days["Date"].dt.date)["Amount"].sum().abs().reset_index()
if not daily_spend.empty:
    fig_line = px.line(daily_spend, x="Date", y="Amount", markers=True, title="Daily Spending")
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("No daily spending to display.")

# Spend vs Save vs Invest Ratios
st.subheader("Spending vs Saving vs Investing Ratios")
df["Day"] = df["Date"].dt.date
pivot = df[df["Category"].isin(["Savings", "Investments"]) | (df["Amount"] < 0)]
pivot["Type"] = pivot["Category"].apply(lambda c: "Spend" if c not in ["Savings", "Investments"] else c)
ratios = pivot.groupby(["Day", "Type"])["Amount"].sum().abs().reset_index()
ratios = ratios.pivot(index="Day", columns="Type", values="Amount").fillna(0).sort_index()
if not ratios.empty:
    fig_ratio = px.area(ratios, title="Daily Financial Flow")
    st.plotly_chart(fig_ratio, use_container_width=True)

    st.markdown("Insights & Tips")
    shown = set()
    for trig in triggers:
        for tip in trigger_to_advice.get(trig, []):
            if tip not in shown:
                st.markdown("- " + tip)
                shown.add(tip)
else:
    st.info("Not enough data to show financial flow.")

# Trigger Frequency Comparison
st.subheader("Behavioral Triggers: This Month vs 2 Months Ago")
df["Month"] = df["Date"].dt.to_period("M")
month_list = df["Month"].sort_values().unique()
if len(month_list) >= 3:
    month_now = month_list[-1]
    month_past = month_list[-3]

    current = derive_behavior_triggers(df[df["Month"] == month_now])
    past = derive_behavior_triggers(df[df["Month"] == month_past])
    combined = list(set(current | past))
    counts = pd.DataFrame({
        "Trigger": combined,
        "Current Month": [1 if t in current else 0 for t in combined],
        "Two Months Ago": [1 if t in past else 0 for t in combined]
    }).set_index("Trigger").T

    diffs = counts.loc["Current Month"] - counts.loc["Two Months Ago"]
    top2 = diffs.abs().sort_values(ascending=False).head(2).index
    fig_trig = px.bar(counts[top2].T.reset_index(), x="Trigger", y=["Current Month", "Two Months Ago"],
                      barmode="group", title="Top Behavioral Trigger Changes")
    st.plotly_chart(fig_trig, use_container_width=True)
else:
    st.info("Not enough data for behavioral trend comparison.")

# Recommended Modules
st.subheader("Recommended Modules")
modules_df["match_score"] = modules_df.apply(lambda row: score_module(row, user_goals, triggers), axis=1)
top_modules = modules_df.sort_values(by="match_score", ascending=False).head(3)
if top_modules["match_score"].max() > 0:
    for title in top_modules["title"]:
        st.markdown(f"- {title}")
else:
    st.info("No relevant modules to recommend right now.")
