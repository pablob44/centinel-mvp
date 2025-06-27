# Centinel – Technical Architecture & Logic

Centinel is a fully modular Streamlit-based MVP designed to simulate a personalized financial literacy platform. It combines behavioral detection, goal-driven content recommendations, token-based progression, and real-time user feedback — all built from scratch using Python, `pandas`, and structured `.csv` data.

The app functions as a local-first prototype, supporting one user per session and writing updates directly into flat files. The logic is built into a single `app.py` with a dynamic routing mechanism that renders one of six main pages: Overview, Analytics, Modules, Shop, Friends, and Profile. All personalization flows from data inputs and behavioral patterns, not hardcoded content.

## User Modeling and State

User state is managed via `user_data.csv`. This file holds the active user’s XP, streak, token balance, premium status, selected goals, and current learning path. These values are accessed on load and are writable from the Profile page. Once the user edits their name, premium status, or goal selections, changes are instantly saved to the CSV and reflected across pages.

All personalization — including module recommendations, challenge selection, and advice — is determined from a combination of `goal_tags`, `behavioral_triggers` detected in recent activity, and missing achievements.

## Behavioral Trigger Detection and Prioritization

The app uses synthetic financial activity (`fake_transactions.csv`) to detect key financial behaviors through rule-based conditions. It scans the past three months of categorized transactions — including savings, investments, subscriptions, and spending — and applies weekly checks for each of eight defined behavioral triggers:

- `high_spending`
- `low_savings`
- `frequent_withdrawals`
- `unstable_income`
- `crypto_interest`
- `subscription_overlap`
- `no_budgeting_history`
- `new_investment_activity`

Each trigger is evaluated weekly over the past three weeks. A dictionary tracks the persistence of each trigger (e.g. a trigger active in all 3 weeks scores highest). The top three persistent triggers are used throughout the system: to deliver advice, rank modules, and suggest challenges.

Separately, the system also identifies **newly activated triggers** — those that appear in the current week but were not active a month ago. These are evaluated for **severity** using heuristics (e.g., total subscription amount, number of withdrawals) and drive the selection of the visualized trigger chart in the Analytics page. If no new trigger exists, it falls back to the most persistent one.

## Module Recommendation Logic

Modules are stored in `modules.csv` and tagged with `goal_tags`, `behavior_triggers`, learning path, access level, exclusivity, and popularity score.

Each module is scored during session runtime using a custom function:

- +1 point for every goal tag that matches the user’s selected goals
- +1 point for every trigger tag that matches the user’s active behavioral triggers

This produces a dynamic score per module. In the Analytics and Overview pages, the top 3 modules (by score) are shown as “Recommended for You”. In the full Modules page, the five highest scoring modules are grouped separately.

Modules are presented in four ordered groups:

1. **Next in path** – The next module in the user’s `current_path`, determined by the lowest unused `module_id`
2. **Featured modules** – Hardcoded promotional content
3. **Recommended modules** – Score-based, dynamic each session
4. **Remaining modules** – Sorted by difficulty level (beginner → advanced)

Modules use color-coded styling:
- Core path modules: varying shades of green
- Featured modules: gold
- External modules: purple (always free)
- Premium modules (flagged as `premium_or_token`): show a lock icon and require premium or tokens to unlock

## Advice Engine

Advice is determined by the top three persistent triggers from the past three weeks. These are mapped 1:1 to short behavioral nudges stored in `centinel_goals_triggers_advice.csv`. Only the advice for the most persistent triggers is shown; no scoring or rotation is applied. The advice is shown in the Analytics page beneath the charts and is intended to be low-effort, behaviorally grounded, and visually secondary.

## Challenge Prioritization Engine

Challenges are stored in `challenges.csv`, each tagged with:
- A linked goal (optional)
- A linked trigger (optional)
- A required achievement (optional)
- XP and token rewards
- Difficulty level

Each challenge is scored per session using a weighted function:

- +2 points if the linked goal is in the user’s goals
- +1 if the linked trigger matches an active trigger
- +1 if the linked achievement has not been unlocked yet

The two highest-scoring challenges are shown on the Overview page as “Weekly Challenges.” A third “Community Challenge” is statically defined and does not depend on user data. These challenges are not yet claimable, but the scaffolding for rewards and visual tracking is implemented.

## Analytics Page Architecture

The Analytics page is the most data-intensive section of the MVP. It pulls in:
- All behavioral trigger scores and persistence counts
- Weekly and daily spending patterns
- Category breakdowns for the past week (pie chart)
- Daily spending values (line chart)
- Area charts showing proportions of spending, saving, and investing
- A dedicated behavioral line chart tied to a single trigger (if newly activated), or the most persistent trigger otherwise

This visual component adjusts based on which trigger has surfaced most recently or with highest severity, using the rules defined in the `trigger_severity()` function.

Advice and top 3 modules (scored as described earlier) are rendered at the bottom of this page. Sidebar content is also populated with trigger persistence summaries and user metadata.

## Other Pages

### Overview

A condensed homepage that includes:
- User’s streak, XP, and token balance
- Their next module in the learning path
- Their top recommended module (by popularity)
- A summary line chart of spending over the past week
- Top 2 weekly challenges + the current community challenge

Modules and analytics previews are clickable and direct the user to those pages via link-style markdown.

### Shop

Displays token balance and available in-app purchases:
- Unlock key for premium modules (10 tokens)
- Avatar customization (coming soon)
- Token bundles (10/50/100) with realistic euro pricing

This page is styled using custom HTML blocks and uses placeholder buttons without live purchase logic.

### Profile

Allows user to update:
- Name
- Goals (via multiselect)
- Premium status (toggle)

Also includes an Achievements section. This compares the user’s unlocked `achievement_ids` (from `user_data.csv`) to the full list (`centinel_achievements_list.csv`) and splits them into “Unlocked” and “Still to Unlock” groups.

### Friends

Loads two additional mock users from `user2_data.csv` and `user3_data.csv`. Shows their streak, XP, and most recent achievement. No interactivity is implemented.

---

Centinel is designed as a rule-based simulation of a behavioral finance app that adapts learning content, feedback, and challenges to the user’s recent activity and progress. It demonstrates how lightweight logic and CSV-based persistence can produce a rich personalized experience with minimal infrastructure.

