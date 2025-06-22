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
    st.title("Personal Finance Dashboard")
    st.metric("Level", xp_data["level"])
    st.metric("XP", xp_data["xp"])
    st.metric("Streak", f"{xp_data['streak_days']} days")
    st.progress(min(xp_data["xp"] % 100 / 100, 1.0))
    
    st.button("Claim Daily XP")
    st.button("View Weekly Report")

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
