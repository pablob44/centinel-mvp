# centinel-mvp
# Centinel – Technical Overview

Centinel is a fully modular personal finance application built in Python using Streamlit. It simulates a complete user experience around financial literacy, behavior tracking, and adaptive learning. The app was developed for a master's project to explore how structured financial behaviors and goals can inform content recommendations and engagement strategies.

The app is routed through a sidebar selector with six main pages: Overview, Analytics, Modules, Shop, Friends, and Profile. Each page is implemented as a block within a single `app.py` file and uses conditional rendering. All data is stored in flat `.csv` files, which are loaded once per session and—when necessary—rewritten directly to preserve user changes (such as editing goals or updating premium status). The MVP supports one user at a time, simulating a personal finance experience end-to-end without requiring user authentication or backend services.

## Personalization and User Modeling

The personalization system is grounded in the user’s stored data (`user_data.csv`). This includes their `goal_tags`, `current_path`, `xp_points`, `streak_days`, `achievements`, and `has_premium` status. Goal tags are used throughout the app to match content to the user's intentions. These goals span a range of financial priorities, such as “save_money”, “start_investing”, and “understand_current_events”. At runtime, this list is parsed and compared with each module's metadata.

The user profile is editable via the Profile page. Users can update their name, toggle premium access, and select or deselect their goal tags via a Streamlit multiselect widget. Changes are immediately written back to the CSV, which ensures that goal-based module recommendations and challenge scoring update across the app with the next session refresh.

## Behavioral Trigger Detection

The behavioral engine is the core logic behind the Analytics and Overview pages. It processes the last three months of transactions stored in `fake_transactions.csv`. This synthetic dataset mimics categorized financial activity including salary, subscriptions, investments, cash withdrawals, and discretionary spending.

To simulate behavioral analysis, a set of predefined rules is used to detect the presence of specific triggers each week. Examples include:

- High discretionary spending if total dining out exceeds €150 in a week.
- Low savings behavior if total savings is below €20.
- Frequent withdrawals if 3+ ATM-like merchants are used in a week.
- Subscription overlap if multiple new subscriptions appear in the same week.

These rules are applied across three rolling weekly windows to track persistence. The three most persistent triggers across the past three weeks are selected for personalized advice, module filtering, and analytics visuals. This logic is encapsulated in a `detect_triggers()` function and a dictionary called `persistence`, which accumulates counts of each active trigger over time.

## Analytics Page Architecture

The Analytics page renders all behavioral insights and decision logic based on the financial data. It begins by identifying which triggers are newly activated this week but were not present a month ago. If multiple new triggers are found, the one with the highest severity is used to drive a dedicated visual. Severity is calculated based on the intensity of the behavior: for instance, high cash withdrawal frequency, low total savings, or overlapping subscriptions.

Once the best behavioral trigger is selected, the page displays a visual specific to that metric. For example:
- For spending: line chart of daily spending totals.
- For subscriptions: line chart of amount spent on subscription merchants.
- For savings: line chart of daily savings amounts.

In addition to the trigger visual, the Analytics page renders a pie chart of total spending by category, a line chart for daily spending across the past week, and an area chart comparing spending, saving, and investing behaviors over time. These are built using Plotly Express, allowing minimal and responsive interactivity.

Finally, the Analytics page shows the top three triggers with their persistence count and uses a mapping file (`centinel_goals_triggers_advice.csv`) to generate one actionable piece of advice per active trigger.

## Module Scoring and Recommendation System

Modules are stored in `modules.csv` and tagged by goal relevance (`goal_tags`), trigger relevance (`behavior_triggers`), access level, and path. When the app loads, a custom scoring function evaluates each module for a given user session. The function adds:
- One point per matching user goal tag
- One point per match with active triggers

Modules with a score above zero are considered recommended. The top three scoring modules are displayed in the Analytics and Overview pages. In the Modules page, the five highest scoring modules are rendered in a “Recommended for You” section. This ensures the app surface adapts based on recent user behavior.

Additionally, each module belongs to a `learning_path` such as “Budgeting Basics” or “Investing Starters”. A path-aware sort function is used to determine the user’s next module in that path by ordering `module_id`s. Featured modules are highlighted separately and shown in gold, while external modules are styled differently and always free.

## Challenges and Progression Logic

The app introduces challenge dynamics via `challenges.csv`, which includes around 40 weekly challenges. Each challenge is tagged with an optional goal, trigger, and achievement ID. For each user session, the app scores the challenge dataset based on two criteria:
- Does the user have the linked goal?
- Has the user already unlocked the linked achievement?

This produces a ranked list of challenge candidates. The top two are displayed in the Overview page as personalized weekly challenges. A third, global “community challenge” is selected manually and hardcoded into the app to ensure variety across weeks.

Each challenge has XP and token rewards, although there is no claiming mechanic implemented in the MVP.

## Module Rendering and Access Control

Modules are rendered in visually distinct boxes based on their type:
- Core modules (based on a learning path) use shades of green.
- Featured modules are colored gold.
- External modules are purple and always free.

Premium modules (marked by the `exclusive` field) show a lock icon and can only be accessed with a key (Shop logic) or premium status. While no unlocking logic is implemented, these visuals and tags are functional and simulate access gating.

## Streamlit Design Philosophy

All elements are built using native Streamlit and minimal custom CSS through `unsafe_allow_html=True` blocks. Pages are self-contained and only share state through the top-level loaded CSVs. All visuals update in real time based on data manipulation in pandas. There is no session state persistence beyond what's stored in the CSVs, which simplifies the app’s internal model while preserving a consistent user experience.

The codebase avoids unnecessary abstraction or function calls in favor of transparency. Each page reads like a narrative from raw data loading to visual output, with behavioral logic and scoring functions embedded inline for clarity.

