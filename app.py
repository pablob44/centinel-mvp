import streamlit as st
import pandas as pd
import plotly.express as px
import json

# --- Load Data ---
with open("xp_progress.json", "r") as f:
    xp_data = json.load(f)

df = pd.read_csv("fake_transactions.csv")

# --- Sidebar ---
st.sidebar.title("Centinel MVP")
st.sidebar.subheader(f"Welcome back, {xp_data['username']}")
st.sidebar.markdown(f"**Level:** {xp_data['level']}")
st.sidebar.markdown(f"**XP:** {xp_data['xp']}")
st.sidebar.markdown(f"**Streak:** {xp_data['streak_days']} days")

# --- Tabs ---
import pandas as pd
import plotly.express as px
import numpy as np

# Load data
df = pd.read_csv("fake_transactions.csv")
user_df = pd.read_csv("centinel_user_data.csv")
modules_df = pd.read_csv("modules.csv")

# --- Behavior trigger function ---
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

# --- Module scoring function ---
def score_module(row):
    goal_tags = user_df.iloc[0]["goal_tags"].split(";")
    triggers = derive_behavior_triggers(df)
    goal_match = len(set(row["goal_tags"].split(";")) & set(goal_tags))
    trigger_match = len(set(row["behavior_triggers"].split(";")) & triggers)
    return goal_match + trigger_match

# --- PAGE 2: ANALYTICS ---
st.title("📊 Spending Analytics")

# --- 1. Last 7 Days Overview ---
st.subheader("Last 7 Days Overview")

df["Date"] = pd.to_datetime(df["Date"])
last_week = df[df["Date"] >= pd.Timestamp.now() - pd.Timedelta(days=7)]

weekly_total = last_week["Amount"].sum()
top_cats = last_week.groupby("Category")["Amount"].sum().sort_values().head(3)

col1, col2 = st.columns(2)
col1.metric("Total Spent", f"€{-weekly_total:.2f}")
col2.metric("Top Category", top_cats.idxmin() if not top_cats.empty else "N/A")

if not top_cats.empty:
    fig_week = px.bar(top_cats.reset_index(), x="Category", y="Amount", title="Top Spending Categories (Last 7 Days)", color="Category")
    st.plotly_chart(fig_week, use_container_width=True)

# --- 2. Full Spending Breakdown (3 Months) ---
st.subheader("Spending Breakdown (Last 3 Months)")
cat_totals = df.groupby("Category")["Amount"].sum().reset_index()
fig_total = px.pie(cat_totals, names="Category", values="Amount")
st.plotly_chart(fig_total, use_container_width=True)

# --- 3. DEV-ONLY: Behavior Triggers ---
triggers = derive_behavior_triggers(df)
st.sidebar.markdown("### 🧠 Behavior Triggers (Dev)")
st.sidebar.write(", ".join(triggers) if triggers else "None")

# --- 4. Recommended Modules ---
st.subheader("📘 Recommended Modules")

modules_df["match_score"] = modules_df.apply(score_module, axis=1)
top_modules = modules_df.sort_values(by="match_score", ascending=False).head(3)

if top_modules["match_score"].max() > 0:
    for title in top_modules["title"]:
        st.markdown(f"- {title}")
else:
    st.info("No relevant modules to recommend right now.")
