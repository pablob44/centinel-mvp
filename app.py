import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
PAGES = {
    "Overview": "overview",
    "Analytics": "analytics",
    "Modules": "modules",
    "Profile": "profile"
}
page = st.sidebar.selectbox("Go to", list(PAGES.keys()))

# --- Load Data ---
df = pd.read_csv("fake_transactions.csv")
df["Date"] = pd.to_datetime(df["Date"])
user_df = pd.read_csv("centinel_user_data.csv")
user = user_df.iloc[0]
modules_df = pd.read_csv("modules.csv")
df_lists = pd.read_csv("centinel_goals_triggers_advice.csv")

# --- Timeframes ---
today = df["Date"].max()
last_3_weeks = [(today - timedelta(days=i*7), today - timedelta(days=(i+1)*7)) for i in range(3)]
month_ago_start = today - timedelta(days=60)
month_ago_end = today - timedelta(days=30)

# --- Trigger Detection ---
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
    if "Budgeting 101" not in modules_df["title"].values:
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

# --- Persistence Calculation ---
persistence = {}
for week_start, week_end in last_3_weeks:
    weekly_data = df[(df["Date"] >= week_end) & (df["Date"] < week_start)]
    week_triggers = detect_triggers(weekly_data)
    for trig in week_triggers:
        persistence[trig] = persistence.get(trig, 0) + 1
top_triggers = sorted(persistence, key=persistence.get, reverse=True)[:3]

# --- Advice Mapping ---
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
if page == "Analytics":
    # --- Visual Trigger Selection ---
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
    
    # --- Module Recommendation ---
    goals = user["goal_tags"].split(";")
    def score_module(row):
        m_goals = row["goal_tags"].split(";")
        m_trigs = row["behavior_triggers"].split(";")
        return len(set(m_goals) & set(goals)) + len(set(m_trigs) & set(top_triggers))
    
    modules_df["score"] = modules_df.apply(score_module, axis=1)
    top_modules = modules_df.sort_values("score", ascending=False).head(3)
    
    # --- Streamlit Layout ---
    st.set_page_config(page_title="Centinel Analytics", layout="wide")
    st.title("Centinel Analytics")
    
    st.sidebar.header(f"Welcome, {user['name']}")
    st.sidebar.markdown(f"Level: {user['level'].capitalize()}")
    st.sidebar.markdown(f"XP: {user['xp_points']} | Streak: {user['streak_days']} days")
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Top Triggers (Past 3 Weeks)**")
    for t in top_triggers:
        st.sidebar.markdown(f"- {t.replace('_',' ').title()} ({persistence[t]}/3 weeks)")
    
    # --- Weekly Overview ---
    st.subheader("Spending Overview (Last 7 Days)")
    latest_date = df["Date"].max()
    last_week = df[df["Date"] >= latest_date - timedelta(days=6)]
    weekly_total = last_week["Amount"].sum()
    top_cats = last_week.groupby("Category")["Amount"].sum().sort_values().head(3)
    col1, col2 = st.columns(2)
    col1.metric("Total Spent", f"€{abs(weekly_total):.2f}")
    col2.metric("Top Category", top_cats.idxmin() if not top_cats.empty else "N/A")
    
    # --- Pie Chart ---
    st.subheader("Spending Breakdown")
    pie_df = df[df["Amount"] < 0]
    cat_totals = pie_df.groupby("Category")["Amount"].sum().abs().reset_index()
    fig_pie = px.pie(cat_totals, names="Category", values="Amount", color_discrete_sequence=px.colors.sequential.Aggrnyl)
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # --- Daily Spending Line Chart ---
    st.subheader("Daily Spending (Past Week)")
    spending_df = df[(df["Date"] >= today - timedelta(days=6)) & (df["Amount"] < 0)]
    daily_spend = spending_df.groupby(spending_df["Date"].dt.date)["Amount"].sum().abs().reset_index()
    fig_line = px.line(daily_spend, x="Date", y="Amount", markers=True, color_discrete_sequence=["#7dd3fc"])
    st.plotly_chart(fig_line, use_container_width=True)
    
    # --- Spend/Save/Invest Ratios ---
    st.subheader("Spending vs Saving vs Investing")
    df["Day"] = df["Date"].dt.date
    pivot = df[df["Category"].isin(["Savings", "Investments"]) | (df["Amount"] < 0)].copy()
    pivot["Type"] = pivot["Category"].apply(lambda c: "Spend" if c not in ["Savings", "Investments"] else c)
    ratios = pivot.groupby(["Day", "Type"])["Amount"].sum().abs().reset_index()
    ratios = ratios.pivot(index="Day", columns="Type", values="Amount").fillna(0).sort_index()
    fig_area = px.area(ratios, color_discrete_sequence=["#7dd3fc", "#34d399"])
    st.plotly_chart(fig_area, use_container_width=True)
    
    # --- Behavioral Trigger Chart ---
    st.subheader(f"Behavior Over Time: {best_trigger.replace('_',' ').title()}" if best_trigger else "Behavior Over Time")
    df["Day"] = df["Date"].dt.date
    if best_trigger == "high_spending":
        plot = df[df["Amount"] < 0].groupby("Day")["Amount"].sum().abs().reset_index()
    elif best_trigger == "low_savings":
        plot = df[df["Category"] == "Savings"].groupby("Day")["Amount"].sum().reset_index()
    elif best_trigger == "frequent_withdrawals":
        plot = df[df["Merchant"].str.contains("ATM|Cash|Venmo|PayPal", case=False, na=False)].groupby("Day")["Amount"].count().reset_index(name="Amount")
    elif best_trigger == "subscription_overlap":
        plot = df[df["Category"] == "Subscriptions"].groupby("Day")["Amount"].sum().reset_index()
    elif best_trigger == "new_investment_activity":
        plot = df[df["Category"] == "Investments"].groupby("Day")["Amount"].sum().reset_index()
    else:
        plot = pd.DataFrame()
    
    if not plot.empty:
        fig = px.line(plot, x="Day", y="Amount", markers=True, color_discrete_sequence=["#7dd3fc"])
        fig.update_layout(yaxis_title="", xaxis_title="", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data to visualize.")
    
    # --- Advice ---
    st.subheader("Advice")
    for t in top_triggers:
        tips = trigger_to_advice.get(t, [])
        if tips:
            st.markdown(f"- {tips[0]}")
    
    # --- Modules ---
    st.subheader("Recommended Modules")
    for _, row in top_modules.iterrows():
        st.markdown(f"- {row['title']}")
elif page == "Modules":
    st.title("Your Learning Modules")

    # --- Data Prep ---
    modules_df["learning_path"] = modules_df["learning_path"].fillna("external")
    modules_df["score"] = modules_df.apply(
        lambda row: len(set(row["goal_tags"].split(";")) & set(user["goal_tags"].split(";")))
        + len(set(row["behavior_triggers"].split(";")) & set(top_triggers)), axis=1
    )

    core_modules = modules_df[modules_df["learning_path"] != "external"]
    current_path = core_modules["learning_path"].iloc[0] if not core_modules.empty else ""
    next_module = core_modules[core_modules["learning_path"] == current_path].sort_values("module_id").head(1)

    featured = modules_df[modules_df["featured"] == True]
    recommended = modules_df[modules_df["score"] > 0].sort_values("score", ascending=False).head(5)
    remaining = modules_df[~modules_df.index.isin(
        next_module.index.union(featured.index).union(recommended.index)
    )].sort_values("access_level")

    def render_module(row):
    tag_color = "#34d399"
    if row["learning_path"] == "external":
        tag_color = "#6b21a8"
    elif row["featured"]:
        tag_color = "#fbbf24"
    premium_lock = " 🔒" if row["exclusive"] == "premium" else ""
    
    return f"""
    <div style='border-left: 6px solid {tag_color}; padding: 1rem 1rem 1rem 1.5rem; background-color: #f9fafb; border-radius: 12px; margin: 0.5rem; color: #111827;'>
        <h4 style='margin-bottom: 0.5rem;'>{row["title"]}{premium_lock}</h4>
        <p style='margin: 0.2rem 0;'><strong>Path:</strong> {row["learning_path"].title()} | <strong>Level:</strong> {row["access_level"].capitalize()}</p>
        <p style='margin: 0.2rem 0;'><strong>XP:</strong> {row["xp_value"]} | <strong>Time:</strong> {row["duration_minutes"]} min | <strong>Popularity:</strong> {row["popularity_score"]:.1f}</p>
    </div>
    """

    def render_module_grid(df, section_title):
        st.subheader(section_title)
        rows = [df.iloc[i:i+3] for i in range(0, len(df), 3)]
        for row_df in rows:
            cols = st.columns(len(row_df))
            for idx, (_, row) in enumerate(row_df.iterrows()):
                with cols[idx]:
                    st.markdown(render_module(row), unsafe_allow_html=True)
    
    # --- Display Sections ---
    render_module_grid(next_module, "Next Module in Your Path")
    render_module_grid(featured, "Featured Modules")
    render_module_grid(recommended, "Recommended for You")
    render_module_grid(remaining, "Explore More Modules")


    # --- Render Sections ---
    st.subheader("Next Module in Your Path")
    for _, row in next_module.iterrows():
        render_module(row)

    st.subheader("Featured Modules")
    for _, row in featured.iterrows():
        render_module(row)

    st.subheader("Recommended for You")
    for _, row in recommended.iterrows():
        render_module(row)

    st.subheader("Explore More Modules")
    for _, row in remaining.iterrows():
        render_module(row)
