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

# Trigger-to-advice mapping
trigger_to_advice = {
    "high_spending": [
        "Try limiting non-essential categories for a week.",
        "High daily spending? Consider batching purchases weekly."
    ],
    "low_savings": [
        "Boost your savings — even small, regular transfers add up over time.",
        "Low savings detected — explore emergency fund strategies.",
        "Consider automating a portion of your income to savings."
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
    ]
}

# Behavioral trigger detection
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

# Module scoring
def score_module(row, user_goals, user_triggers):
    module_goals = row["goal_tags"].split(";")
    module_triggers = row["behavior_triggers"].split(";")
    goal_match = len(set(module_goals) & set(user_goals))
    trigger_match = len(set(module_triggers) & set(user_triggers))
    return goal_match + trigger_match

# Load user
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

# Fallback to recent week with data
recent_spending = df[df["Amount"] < 0].sort_values("Date", ascending=False)
if not recent_spending.empty:
    latest_date = recent_spending["Date"].max()
    last_week = df[(df["Date"] >= latest_date - timedelta(days=6)) & 
                   (df["Date"] <= latest_date)]
else:
    last_week = pd.DataFrame()

weekly_total = last_week["Amount"].sum() if not last_week.empty else 0
top_cats = last_week.groupby("Category")["Amount"].sum().sort_values().head(3) if not last_week.empty else pd.Series()

col1, col2 = st.columns(2)
col1.metric("Total Spent", f"€{abs(weekly_total):.2f}")
col2.metric("Top Category", top_cats.idxmin() if not top_cats.empty else "N/A")

# Bar chart for spending breakdown (3 months)
st.subheader("Spending by Category (Bar Chart)")
exclude_categories = ["Salary", "Savings", "Investments"]
spending_df = df[~df["Category"].isin(exclude_categories)]
cat_totals = spending_df.groupby("Category")["Amount"].sum().abs().reset_index()
if not cat_totals.empty:
    fig_bar = px.bar(cat_totals.sort_values("Amount", ascending=False),
                     x="Category", y="Amount", title="Category Spending (Last 3 Months)")
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.info("No spending data available for category breakdown.")

# Daily Spending (Line)
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

    # Simple advice section
    st.markdown("Insights & Tips")
    shown = set()
    for trig in triggers:
        for tip in trigger_to_advice.get(trig, []):
            if tip not in shown:
                st.markdown("- " + tip)
                shown.add(tip)
else:
    st.info("Not enough data to show financial flow.")

# Compare behavior change over months
st.subheader("Behavior Trend: This Month vs 2 Months Ago")
df["Month"] = df["Date"].dt.to_period("M")
filtered = df[df["Amount"] < 0]
month_summary = filtered.groupby(["Month", "Category"])["Amount"].sum().reset_index()
if month_summary["Month"].nunique() >= 3:
    last_two = month_summary["Month"].unique()[-3::2]  # current and 2 months ago
    compare = month_summary[month_summary["Month"].isin(last_two)]
    fig_compare = px.bar(compare, x="Category", y="Amount", color="Month",
                         barmode="group", title="Spending by Category Comparison")
    st.plotly_chart(fig_compare, use_container_width=True)
else:
    st.info("Not enough data to compare category behavior over time.")

# Recommended Modules
st.subheader("Recommended Modules")
modules_df["match_score"] = modules_df.apply(lambda row: score_module(row, user_goals, triggers), axis=1)
top_modules = modules_df.sort_values(by="match_score", ascending=False).head(3)
if top_modules["match_score"].max() > 0:
    for title in top_modules["title"]:
        st.markdown(f"- {title}")
else:
    st.info("No relevant modules to recommend right now.")
