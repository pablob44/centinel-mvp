import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- Load Data ---
df = pd.read_csv("fake_transactions.csv")
df["Date"] = pd.to_datetime(df["Date"])

user_df = pd.read_csv("centinel_user_data.csv")
modules_df = pd.read_csv("modules.csv")

# --- Behavior Trigger Logic ---
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

# --- Module Scoring ---
def score_module(row, user_goals, user_triggers):
    module_goals = row["goal_tags"].split(";")
    module_triggers = row["behavior_triggers"].split(";")
    goal_match = len(set(module_goals) & set(user_goals))
    trigger_match = len(set(module_triggers) & set(user_triggers))
    return goal_match + trigger_match

# --- App Layout ---
st.set_page_config(page_title="Centinel - Analytics", layout="wide")
st.title("📊 Spending Analytics")

# --- Load User Info ---
user = user_df.iloc[0]
user_goals = user["goal_tags"].split(";")
user_triggers = derive_behavior_triggers(df)

# --- Sidebar (Developer Notes) ---
st.sidebar.title("Centinel MVP")
st.sidebar.subheader(f"Welcome back, {user['name']}")
st.sidebar.markdown(f"**Level:** {user['level'].capitalize()}")
st.sidebar.markdown(f"**XP:** {user['xp_points']}")
st.sidebar.markdown(f"**Streak:** {user['streak_days']} days")
st.sidebar.markdown("---")
st.sidebar.markdown("### 🧠 Behavior Triggers (Dev Only)")
st.sidebar.write(", ".join(user_triggers) if user_triggers else "None")

# --- 1. Last 7 Days Overview ---
st.subheader("📅 Last 7 Days Overview")

recent_df = df[df["Date"] >= pd.Timestamp.now() - pd.Timedelta(days=7)]
weekly_total = recent_df["Amount"].sum()
top_cats = recent_df.groupby("Category")["Amount"].sum().sort_values().head(3)

col1, col2 = st.columns(2)
col1.metric("Total Spent", f"€{-weekly_total:.2f}")
col2.metric("Top Category", top_cats.idxmin() if not top_cats.empty else "N/A")

if not top_cats.empty:
    fig_week = px.bar(top_cats.reset_index(), x="Category", y="Amount",
                      title="Top Spending Categories (Last 7 Days)", color="Category")
    st.plotly_chart(fig_week, use_container_width=True)

# --- 2. 3-Month Spending Breakdown ---
st.subheader("📊 Spending Breakdown (Last 3 Months)")
cat_totals = df.groupby("Category")["Amount"].sum().reset_index()
fig_total = px.pie(cat_totals, names="Category", values="Amount", title="Spending by Category")
st.plotly_chart(fig_total, use_container_width=True)

# --- 3. Module Recommendations (Compact) ---
st.subheader("📘 Recommended Modules")

modules_df["match_score"] = modules_df.apply(lambda row: score_module(row, user_goals, user_triggers), axis=1)
top_modules = modules_df.sort_values(by="match_score", ascending=False).head(3)

if top_modules["match_score"].max() > 0:
    for title in top_modules["title"]:
        st.markdown(f"- {title}")
else:
    st.info("No relevant modules to recommend right now.")

