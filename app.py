import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Load data
df = pd.read_csv("fake_transactions.csv")
df["Date"] = pd.to_datetime(df["Date"])
user = pd.read_csv("centinel_user_data.csv").iloc[0]
modules = pd.read_csv("modules.csv")
df_lists = pd.read_csv("centinel_goals_triggers_advice.csv")

# Define timeframes
today = df["Date"].max()
last_3_weeks = [(today - timedelta(days=i*7), today - timedelta(days=(i+1)*7)) for i in range(3)]
month_ago_start = today - timedelta(days=60)
month_ago_end = today - timedelta(days=30)

# Trigger detection (binary logic)
def detect_triggers(data):
    triggers = set()
    if data[data["Category"] == "Dining Out"]["Amount"].sum() < -150:
        triggers.add("high_spending")
    if data[data["Category"] == "Savings"]["Amount"].sum() < 20:
        triggers.add("low_savings")
    if data["Merchant"].str.contains("Crypto Wallet", na=False).any():
        triggers.add("crypto_interest")
    if data["Merchant"].str.contains("ATM|Venmo|Cash|PayPal", case=False, na=False).sum() >= 3:
        triggers.add("frequent_withdrawals")
    if "Budgeting 101" not in modules["title"].values:
        triggers.add("no_budgeting_history")
    if "Index ETF" in data["Merchant"].values:
        triggers.add("new_investment_activity")
    salary_months = data[data["Category"] == "Salary"]["Date"].dt.to_period("M").nunique()
    if salary_months < 2:
        triggers.add("unstable_income")
    subs = data[data["Category"] == "Subscriptions"].copy()
    subs["Week"] = subs["Date"].dt.to_period("W")
    if subs.groupby("Week")["Merchant"].nunique().max() >= 2:
        triggers.add("subscription_overlap")
    return triggers

# Weekly persistence: how many weeks each trigger was active
persistence = {}
for week_start, week_end in last_3_weeks:
    weekly_data = df[(df["Date"] >= week_end) & (df["Date"] < week_start)]
    week_triggers = detect_triggers(weekly_data)
    for trig in week_triggers:
        persistence[trig] = persistence.get(trig, 0) + 1

# Top 3 persistent triggers
top_triggers = sorted(persistence, key=persistence.get, reverse=True)[:3]

# Trigger-to-advice mapping
trigger_to_advice = {
    "high_spending": ["Try limiting non-essential categories for a week."],
    "low_savings": ["Boost your savings — even small, regular transfers add up over time."],
    "crypto_interest": ["Crypto detected — just make sure it fits your long-term plan."],
    "frequent_withdrawals": ["Frequent withdrawals may signal poor planning. Try setting weekly limits."],
    "no_budgeting_history": ["No budgeting history — start simple with a 50/30/20 method."],
    "new_investment_activity": ["New investment detected — diversify gradually if you're just starting out."],
    "unstable_income": ["Your income looks inconsistent. Try building a savings buffer."],
    "subscription_overlap": ["Multiple subscriptions overlap — consider cancelling one unused service."]
}

# Detect new triggers and decide visual
current_week = df[df["Date"] > today - timedelta(days=7)]
past_month = df[(df["Date"] >= month_ago_start) & (df["Date"] < month_ago_end)]
new_now = detect_triggers(current_week)
old = detect_triggers(past_month)
new_triggers = new_now - old

def trigger_severity(trigger, data):
    if trigger == "high_spending":
        return abs(data[data["Amount"] < 0]["Amount"].sum())
    elif trigger == "low_savings":
        return abs(data[data["Category"] == "Savings"]["Amount"].sum())
    elif trigger == "frequent_withdrawals":
        return data["Merchant"].str.contains("ATM|Cash|Venmo|PayPal", case=False, na=False).sum()
    elif trigger == "subscription_overlap":
        subs = data[data["Category"] == "Subscriptions"]
        return subs["Amount"].sum() if not subs.empty else 0
    elif trigger == "new_investment_activity":
        return data[data["Category"] == "Investments"]["Amount"].sum()
    return 0

candidate_triggers = list(new_triggers & {"high_spending", "low_savings", "frequent_withdrawals", "subscription_overlap", "new_investment_activity"})
if candidate_triggers:
    best_trigger = max(candidate_triggers, key=lambda t: trigger_severity(current_week, t))
else:
    fallback_triggers = [t for t in top_triggers if t in {"high_spending", "low_savings", "frequent_withdrawals", "subscription_overlap", "new_investment_activity"}]
    best_trigger = fallback_triggers[0] if fallback_triggers else None

# Recommend modules
user_goals = user["goal_tags"].split(";")
def score_module(row):
    m_goals = row["goal_tags"].split(";")
    m_trigs = row["behavior_triggers"].split(";")
    return len(set(m_goals) & set(user_goals)) + len(set(m_trigs) & set(top_triggers))

modules["score"] = modules.apply(score_module, axis=1)
top_modules = modules.sort_values("score", ascending=False).head(3)

# --- Streamlit Layout ---
st.set_page_config(page_title="Centinel Analytics", layout="wide")
st.title("Centinel Analytics")

# Sidebar user summary
st.sidebar.header(f"Welcome, {user['name']}")
st.sidebar.markdown(f"Level: {user['level'].capitalize()}")
st.sidebar.markdown(f"XP: {user['xp_points']} | Streak: {user['streak_days']} days")
st.sidebar.markdown("---")
st.sidebar.markdown("**Top Triggers (Past 3 Weeks)**")
for t in top_triggers:
    st.sidebar.markdown(f"- {t.replace('_',' ').title()} ({persistence[t]}/3 weeks)")

# Visual display
st.subheader(f"Behavior Over Time: {best_trigger.replace('_',' ').title()}" if best_trigger else "Behavior Over Time")
if best_trigger:
    df["Day"] = df["Date"].dt.date
    if best_trigger == "high_spending":
        plot_df = df[df["Amount"] < 0].groupby("Day")["Amount"].sum().abs().reset_index()
    elif best_trigger == "low_savings":
        plot_df = df[df["Category"] == "Savings"].groupby("Day")["Amount"].sum().reset_index()
    elif best_trigger == "frequent_withdrawals":
        plot_df = df[df["Merchant"].str.contains("ATM|Cash|Venmo|PayPal", case=False, na=False)]
        plot_df = plot_df.groupby("Day")["Amount"].count().reset_index(name="Amount")
    elif best_trigger == "subscription_overlap":
        plot_df = df[df["Category"] == "Subscriptions"].groupby("Day")["Amount"].sum().reset_index()
    elif best_trigger == "new_investment_activity":
        plot_df = df[df["Category"] == "Investments"].groupby("Day")["Amount"].sum().reset_index()
    else:
        plot_df = pd.DataFrame()

    if not plot_df.empty:
        fig = px.line(plot_df, x="Day", y="Amount", markers=True,
                      color_discrete_sequence=["#7dd3fc", "#34d399"])  # light blue / green
        fig.update_layout(yaxis_title="", xaxis_title="", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data to visualize this behavior.")

# Advice
st.subheader("Advice")
for t in top_triggers:
    tips = trigger_to_advice.get(t, [])
    if tips:
        st.markdown(f"- {tips[0]}")

# Recommended modules
st.subheader("Recommended Modules")
for _, row in top_modules.iterrows():
    st.markdown(f"- {row['title']}")
