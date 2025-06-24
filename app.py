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
# Add this below your existing imports
import numpy as np

# Load additional data
user_df = pd.read_csv("centinel_user_data.csv")
modules_df = pd.read_csv("modules.csv")

# Derive behavior triggers from spending
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

# --- Page 2: Analytics ---
with st.expander("🔍 Analytics", expanded=True):
    st.header("Financial Insights & Recommendations")

    # Spending Breakdown
    cat_totals = df.groupby("Category")["Amount"].sum().reset_index()
    fig = px.pie(cat_totals, names="Category", values="Amount", title="Spending Breakdown (Past 3 Months)")
    st.plotly_chart(fig)

    # User info
    user_goals = user_df.iloc[0]["goal_tags"].split(";")
    st.markdown("### Your Goals:")
    st.write(", ".join(user_goals))

    # Derive triggers from transactions
    triggers = derive_behavior_triggers(df)
    st.markdown("### Behavioral Triggers Detected:")
    st.write(", ".join(triggers) if triggers else "None")

    # Recommend Modules
    def score_module(row):
        goal_match = len(set(row["goal_tags"].split(";")) & set(user_goals))
        trigger_match = len(set(row["behavior_triggers"].split(";")) & triggers)
        return goal_match + trigger_match

    modules_df["match_score"] = modules_df.apply(score_module, axis=1)
    top_recommendations = modules_df.sort_values(by="match_score", ascending=False).head(5)

    st.markdown("### Recommended Modules")
    for _, row in top_recommendations.iterrows():
        st.markdown(f"**{row['title']}**  \n*Topic:* {row['topic_area']}  \n*XP:* {row['xp_value']}  \n*Duration:* {row['duration_minutes']} min  \n---")
