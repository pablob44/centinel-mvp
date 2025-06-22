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
tab1, tab2, tab3 = st.tabs(["Home", "Bank Analytics", "Learning Hub"])

# --- Home Tab ---
with tab1:
    st.title("Welcome to Centinel")
    st.markdown("Your all-in-one hub for financial progress, habits, and personal growth.")

    # Key Stats Row
    col1, col2, col3 = st.columns(3)
    col1.metric("Level", xp_data["level"])
    col2.metric("XP", xp_data["xp"])
    col3.metric("Streak", f"{xp_data['streak_days']} days")

    st.progress(min(xp_data["xp"] % 100 / 100, 1.0), text="Progress to next level")

    st.divider()

    # Weekly Financial Summary
    st.subheader("Weekly Financial Summary")
    total_income = df[df["Amount"] > 0]["Amount"].sum()
    total_expenses = df[df["Amount"] < 0]["Amount"].sum()
    total_savings_tx = df[df["Category"] == "Savings"]["Amount"].sum()
    net_savings = total_income + total_expenses  # expenses are negative

    col4, col5, col6 = st.columns(3)
    col4.metric("Total Income", f"€{total_income:.2f}")
    col5.metric("Total Expenses", f"€{abs(total_expenses):.2f}")
    col6.metric("Net Savings (Calc)", f"€{net_savings:.2f}")

    st.metric("Savings Transfers (Tagged)", f"€{total_savings_tx:.2f}")

    fig = px.pie(df, values="Amount", names="Category", title="Spending by Category")
    st.plotly_chart(fig)

    st.divider()

    # Quick Access
    st.subheader("Quick Access")
    col6, col7 = st.columns(2)
    with col6:
        st.button("Claim Daily XP")
        st.button("View Weekly Report")
    with col7:
        st.button("Connect Bank Account")
        st.button("Start New Module")

# --- Bank Analytics Tab ---
with tab2:
    st.title("Spending Breakdown")
    st.dataframe(df)

    fig = px.pie(df, values="Amount", names="Category", title="Spending by Category")
    st.plotly_chart(fig)

    total_spent = df[df["Amount"] < 0]["Amount"].sum()
    total_saved = df[df["Amount"] > 0]["Amount"].sum()
    st.metric("Total Spent", f"€{abs(total_spent):.2f}")
    st.metric("Total Saved", f"€{total_saved:.2f}")

# --- Learning Hub Tab ---
with tab3:
    st.title("Gamified Learning Hub")
    topics = ["Budgeting Basics", "How Credit Works", "Crypto 101", "Smart Saving Tips"]
    cols = st.columns(2)
    for i, topic in enumerate(topics):
        with cols[i % 2]:
            st.button(topic)
