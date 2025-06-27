import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
PAGES = {
    "Overview": "overview",
    "Analytics": "analytics",
    "Modules": "modules",
    "Shop": "shop",
    "Friends": "friends",
    "Profile": "profile"
}
st.sidebar.markdown("## Navigation")
page = st.sidebar.radio("", list(PAGES.keys()))

# Optional: highlight current page with a subtle color (pseudo-style)
def highlight(label):
    return f"<span style='color:#22d3ee;font-weight:bold'>{label}</span>"


# --- User Selection ---
USER_FILES = {
    "U001": {"user": "user_data.csv", "transactions": "fake_transactions.csv"},
    "U002": {"user": "user2_data.csv", "transactions": "fake_transactions2.csv"}
}

with st.sidebar:
    selected_user = st.selectbox("Switch User", list(USER_FILES.keys()), index=0)

# --- Load Selected User Data ---
user_df = pd.read_csv(USER_FILES[selected_user]["user"])
df = pd.read_csv(USER_FILES[selected_user]["transactions"])
df["Date"] = pd.to_datetime(df["Date"])
user = user_df.iloc[0]
modules_df = pd.read_csv("modules.csv")
df_lists = pd.read_csv("centinel_goals_triggers_advice.csv")
if page != "Overview" and page != "Analytics":
    st.sidebar.markdown("---")
    st.sidebar.header(f"Welcome, {user['name']}")
    st.sidebar.markdown(f"Level: {user['level'].capitalize()}")
    st.sidebar.markdown(f"XP: {user['xp_points']} | Streak: {user['streak_days']} days")


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

    # --- Set access_level as ordered categorical for sorting
    difficulty_order = ["beginner", "intermediate", "advanced"]
    modules_df["access_level"] = modules_df["access_level"].str.lower().fillna("beginner")
    modules_df["access_level"] = pd.Categorical(modules_df["access_level"], categories=difficulty_order, ordered=True)

    core_modules = modules_df[modules_df["learning_path"] != "external"]
    current_path = core_modules["learning_path"].iloc[0] if not core_modules.empty else ""
    next_module = core_modules[core_modules["learning_path"] == current_path].sort_values("module_id").head(1)

    featured = modules_df[modules_df["featured"] == True]
    recommended = modules_df[modules_df["score"] > 0].sort_values("score", ascending=False).head(5)
    remaining = modules_df[~modules_df.index.isin(
        next_module.index.union(featured.index).union(recommended.index)
    )].sort_values("access_level")

    # --- Color map by path (green variations), override for premium and external
    path_colors = {
        "Budgeting Basics": "#6ee7b7",
        "Financial Resilience": "#34d399",
        "Investing Starters": "#059669",
        "external": "#6b21a8",
    }

    def render_module(row):
        # Premium logic + override color
        is_premium = row["exclusive"] == "premium_or_token"
        tag_color = path_colors.get(row["learning_path"], "#34d399")
        if is_premium:
            tag_color = "#fbbf24"  # gold

        premium_lock = " 🔒" if is_premium else ""

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

    # --- Display All Sections ---
    render_module_grid(next_module, "Next Module in Your Path")
    render_module_grid(featured, "Featured Modules")
    render_module_grid(recommended, "Recommended for You")
    render_module_grid(remaining, "Explore More Modules")
elif page == "Shop":
    st.title(" Centinel Shop")

    # --- Token Balance ---
    token_balance = int(user["token_balance"]) if "token_balance" in user else 0
    st.markdown(f"###  Your Token Balance: **{token_balance}**")
    st.markdown("---")

    # --- Unlock Module Key ---
    st.markdown("""
    <div style='border: 2px solid #4ade80; border-radius: 12px; padding: 1rem; margin-bottom: 1rem; background-color: #f0fdf4;color: #111827;'>
        <h4>🔑 Unlock Module Key</h4>
        <p>Use this key to unlock any premium or token-only module.</p>
        <p><strong>Price:</strong> 10 tokens</p>
        <button disabled style='padding: 0.5rem 1rem; background-color: #22c55e; color: white; border: none; border-radius: 6px; cursor: not-allowed;'>Buy Now</button>
    </div>
    """, unsafe_allow_html=True)

    # --- Avatar Customisation (Not Available) ---
    st.markdown("""
    <div style='border: 2px solid #a855f7; border-radius: 12px; padding: 1rem; margin-bottom: 1rem; background-color: #f3e8ff;color: #111827;'>
        <h4> Avatar Customisation</h4>
        <p>Personalise your profile with visual upgrades.</p>
        <p><strong>Coming Soon</strong></p>
        <button disabled style='padding: 0.5rem 1rem; background-color: #9333ea; color: white; border: none; border-radius: 6px; cursor: not-allowed;'>Coming Soon</button>
    </div>
    """, unsafe_allow_html=True)

    # --- Token Bundles ---
    st.subheader(" Buy More Tokens")
    bundles = [
        {"tokens": 10, "price": 4.99},
        {"tokens": 50, "price": 19.99},
        {"tokens": 100, "price": 34.99}
    ]

    cols = st.columns(3)
    for col, bundle in zip(cols, bundles):
        with col:
            st.markdown(f"""
            <div style='border: 2px solid #38bdf8; border-radius: 12px; padding: 1rem; background-color: #f0f9ff; color: #0f172a;'>
                <h4> {bundle["tokens"]} Tokens</h4>
                <p style='margin: 0.2rem 0;'><strong>Price:</strong> €{bundle["price"]:.2f}</p>
                <button disabled style='padding: 0.4rem 1rem; background-color: #0ea5e9; color: white; border: none; border-radius: 6px; cursor: not-allowed;'>Buy Now</button>
            </div>
            """, unsafe_allow_html=True)
elif page == "Friends":
    st.title(" My Friends")

    # --- Load All Users ---
    all_users = {
        "U001": pd.read_csv("user_data.csv").iloc[0],
        "U002": pd.read_csv("user2_data.csv").iloc[0],
        "U003": pd.read_csv("user3_data.csv").iloc[0],
    }

    # --- Select only friends (exclude current user by user_id) ---
    current_user_id = user["user_id"]  # Always available in user_df
    friends = [data for uid, data in all_users.items() if uid != current_user_id]

    # --- Friend Card Renderer ---
    def render_friend(friend_user):
        latest_achievement = friend_user["achievements"].split(";")[-1]
        st.markdown(f"""
        <div style='border-left: 6px solid #4ade80; background-color: #f0fdf4; padding: 1rem 1.5rem; border-radius: 10px; margin-bottom: 1rem; color: #111827;'>
            <h4>{friend_user["name"]}</h4>
            <p><strong>Streak:</strong> {friend_user["streak_days"]} days</p>
            <p><strong>XP:</strong> {friend_user["xp_points"]}</p>
            <p><strong>Latest Achievement:</strong> {latest_achievement.replace("_", " ").capitalize()}</p>
        </div>
        """, unsafe_allow_html=True)

    # --- Render All Friends ---
    for f in friends:
        render_friend(f)


elif page == "Profile":
    st.title("Your Profile")

    # --- Load Achievements List ---
    achievements_df = pd.read_csv("centinel_achievements_list.csv")

    # --- Profile Overview ---
    st.markdown(f"**Name:** {user['name']}")
    st.markdown(f"**Level:** {user['level'].capitalize()}")
    st.markdown(f"**XP:** {user['xp_points']}")
    st.markdown(f"**Streak:** {user['streak_days']} days")
    st.markdown(f"**Token Balance:** {user['token_balance']}")
    st.markdown(f"**Current Path:** {user['current_path']}")
    if user['has_premium'] == True or str(user['has_premium']).lower() == "true":
        st.success("Premium User")
    st.markdown("---")

    # --- Edit Profile Section ---
    with st.expander("✏️ Edit Profile"):
        updated_name = st.text_input("Update your name", value=user["name"])
        
        goal_options = [
            "save_money", "get_financial_control", "start_investing", "reduce_debt", "spend_better",
            "build_savings_buffer", "budget_consistently", "optimize_subscriptions", "boost_income",
            "understand_credit", "avoid_scam_investments", "understand_current_events", "learn_finance_history",
            "decode_inflation", "understand_investing_terms", "learn_wealth_inequality", "get_news_literacy"
        ]
        current_goals = user["goal_tags"].split(";")
        updated_goals = st.multiselect("Select your goals", goal_options, default=current_goals)

        # Premium toggle
        premium_toggle = st.checkbox("Upgrade to Premium" if not user["has_premium"] else "Deactivate Premium", value=bool(user["has_premium"]))

        if st.button("Save Changes"):
            user_df.loc[0, "name"] = updated_name
            user_df.loc[0, "goal_tags"] = ";".join(updated_goals)
            user_df.loc[0, "has_premium"] = premium_toggle
            user_df.to_csv("user_data.csv", index=False)
            st.success("Profile updated! Changes will apply on next refresh.")

    st.markdown("---")

    # --- Achievements Display ---
    with st.expander(" Your Achievements"):
        unlocked = user["achievements"].split(";")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Unlocked")
            for ach in achievements_df.itertuples():
                if ach.id in unlocked:
                    st.markdown(f" **{ach.description}**  `({ach.category})`")

        with col2:
            st.subheader("Still to Unlock")
            for ach in achievements_df.itertuples():
                if ach.id not in unlocked:
                    st.markdown(f" *{ach.description}*  `({ach.category})`")
elif page == "Overview":
    st.set_page_config(page_title="Centinel Overview", layout="wide")
    st.title("Welcome back, " + user["name"])

    # --- Load Challenges ---
    challenges_df = pd.read_csv("challenges.csv")
    community_challenge = {
        'challenge_id': 'COMM002',
        'challenge_text': 'Log into the app every day this week.',
        'linked_goal': '',
        'linked_trigger': '',
        'linked_achievement': '',
        'estimated_difficulty': 'hard',
        'xp_reward': 80,
        'token_reward': 3
    }

    # --- Challenge Scoring ---
    
    goals = set(user["goal_tags"].split(";"))
    achievements = set(user["achievements"].split(";"))
    triggers = set(top_triggers)  # from previous logic in analytics
    
    def challenge_score(row):
        score = 0
        if row["linked_goal"] in goals:
            score += 2
        if row["linked_trigger"] in triggers:
            score += 1
        if row["linked_achievement"] not in achievements and pd.notna(row["linked_achievement"]):
            score += 1
        return score
    
    challenges_df["score"] = challenges_df.apply(challenge_score, axis=1)
    top_challenges = challenges_df.sort_values("score", ascending=False).head(2)


    # --- Next Module ---
    path_modules = modules_df[modules_df["learning_path"] == user["current_path"]]
    next_module = path_modules.sort_values("module_id").head(1)
    recommended_module = modules_df.sort_values("popularity_score", ascending=False).head(1)

    # --- Weekly Spending Chart ---
    latest_day = df["Date"].max()
    last_week_df = df[(df["Date"] >= latest_day - timedelta(days=6)) & (df["Amount"] < 0)]
    daily_spend = last_week_df.groupby(df["Date"].dt.date)["Amount"].sum().abs().reset_index()
    fig_spend = px.line(daily_spend, x="Date", y="Amount", markers=True,
                        title="Spending Last 7 Days",
                        color_discrete_sequence=["#22d3ee"])
    fig_spend.update_layout(xaxis_title="", yaxis_title="Amount", showlegend=False)

    # --- User Summary ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Streak", f"{user['streak_days']} days")
    col2.markdown(f"[Tokens: {user['token_balance']}](#Shop)")
    col3.metric("XP", f"{user['xp_points']}")

    # --- Modules Section ---
   # --- Score Modules Based on Goals and Triggers ---
    def score_module(row):
        m_goals = set(row["goal_tags"].split(";"))
        m_trigs = set(row["behavior_triggers"].split(";"))
        return len(m_goals & goals) + len(m_trigs & triggers)
    
    modules_df["score"] = modules_df.apply(score_module, axis=1)
    top_scored_module = modules_df.sort_values("score", ascending=False).head(1)
    
    # --- Next Module in Learning Path ---
    path_modules = modules_df[modules_df["learning_path"] == user["current_path"]]
    next_module = path_modules.sort_values("module_id").head(1)
    
    # --- Display Modules ---
    st.markdown("### Your Next Module")
    if not next_module.empty:
        m = next_module.iloc[0]
        st.markdown(f"**{m['title']}**  \n{m['learning_path']} – {m['access_level'].capitalize()}")
    
    st.markdown("### Recommended Module for You")
    if not top_scored_module.empty:
        top_m = top_scored_module.iloc[0]
        st.markdown(f"**{top_m['title']}**  \n{top_m['learning_path']} – {top_m['access_level'].capitalize()}  \nXP: {top_m['xp_value']} | Duration: {top_m['duration_minutes']} min")

    # --- Analytics Preview ---
    st.markdown("### Weekly Snapshot")
    st.plotly_chart(fig_spend, use_container_width=True)
    st.markdown("[View full analytics ➜](#Analytics)")

    # --- Challenges ---
    st.markdown("### Weekly Challenges")
    for _, ch in top_challenges.iterrows():
        st.markdown(f"- **{ch['challenge_text']}**  \nXP: {ch['xp_reward']} | Tokens: {ch['token_reward']}")

    st.markdown("### Community Challenge")
    st.markdown(f"- **{community_challenge['challenge_text']}**  \nXP: {community_challenge['xp_reward']} | Tokens: {community_challenge['token_reward']}")

