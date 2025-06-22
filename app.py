
import streamlit as st
import pandas as pd
import plotly.express as px
import json

# Load XP progress
with open("xp_progress.json", "r") as f:
    xp_data = json.load(f)

# Load transaction data
df = pd.read_csv("fake_transactions.csv")

# --- Sidebar User Greeting ---
st.sidebar.image("https://i.imgur.com/wx2jdkl.png", width=100)
st.sidebar.title(f"Welcome back, {xp_data['username']}!")
st.sidebar.markdown(f"**Level:** {xp_data['level']}  
**XP:** {xp_data['xp']}  
🔥 Streak: {xp_data['streak_days']} days")

# --- Main Tabs ---
tab1, tab2, tab3 = st.tabs(["🏠 Home", "📊 Bank Analytics", "🎯 Learning Hub"])

# --- Home Page ---
with tab1:
    st.title("Your Financial Command Center")
    st.markdown("This is your **personalized homepage** with key highlights:")

    col1, col2, col3 = st.columns(3)
    col1.metric("Level", xp_data["level"])
    col2.metric("XP", xp_data["xp"])
    col3.metric("🔥 Streak", f"{xp_data['streak_days']} days")

    st.progress(min(xp_data["xp"] % 100 / 100, 1.0), text="Progress to next level")

    st.subheader("Quick Actions")
    st.button("🏆 Claim Daily XP")
    st.button("📈 View Weekly Report")

# --- Bank Analytics ---
with tab2:
    st.title("Spending Overview")
    st.markdown("Below is a breakdown of your recent transactions:")

    st.dataframe(df)

    fig = px.pie(df, values="Amount", names="Category", title="Spending Distribution by Category")
    st.plotly_chart(fig)

    total_spent = df[df["Amount"] < 0]["Amount"].sum()
    total_saved = df[df["Amount"] > 0]["Amount"].sum()
    st.metric("💸 Total Spent", f"€{abs(total_spent):.2f}")
    st.metric("💰 Total Saved", f"€{total_saved:.2f}")

# --- Learning Hub ---
with tab3:
    st.title("Gamified Learning Hub")
    st.markdown("Choose a topic to explore and earn XP!")

    topics = ["Budgeting Basics", "How Credit Works", "Crypto 101", "Smart Saving Tips"]
    cols = st.columns(2)

    for i, topic in enumerate(topics):
        with cols[i % 2]:
            st.button(f"📚 {topic}")
