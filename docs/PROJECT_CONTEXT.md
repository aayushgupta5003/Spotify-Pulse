# Spotify Pulse — Project Context

## 1. Project Overview

Spotify Pulse is a Spotify-inspired Product Analytics and Data Science
platform built as a portfolio project.

The project is intended to demonstrate practical skills across:

- Data Engineering
- Data Cleaning
- SQL Analytics
- Exploratory Data Analysis
- Product Analytics
- User Behavior Analysis
- Machine Learning
- User Segmentation
- Churn Prediction
- Experimentation / A-B Testing
- Business Insight Generation
- Streamlit Dashboarding

The goal is to build one coherent analytics product rather than a
collection of disconnected notebooks.

The final system should allow an analyst or product manager to understand:

- how users engage with the platform
- how listening behavior differs across user groups
- what factors are associated with churn
- how users can be segmented
- how preferences relate to behavior
- how recommendation experiences can be evaluated
- how product experiments can be analyzed
- what product opportunities emerge from the analysis

---

# 2. Project Philosophy

The project should follow this analytical flow:

Business Question
        ↓
Data
        ↓
Data Quality
        ↓
Data Modeling
        ↓
SQL / Analytics
        ↓
EDA
        ↓
Feature Engineering
        ↓
ML / Experimentation
        ↓
Product Insights
        ↓
Dashboard

Avoid producing random visualizations without a business question.

The preferred analytical approach is:

Business Hypothesis
        ↓
EDA / Statistical Analysis
        ↓
Evidence
        ↓
Insight
        ↓
Potential Product Decision

Hypotheses must be tested rather than presented as established facts.

---

# 3. Source Datasets

The project uses three primary datasets.

## 3.1 Spotify Streaming History

File:

`data/raw/spotify_streaming_history.csv`

Approximate size:

149,860 rows before cleaning.

Columns:

- spotify_track_uri
- ts
- platform
- ms_played
- track_name
- artist_name
- album_name
- reason_start
- reason_end
- shuffle
- skipped

This is event-level listening data.

Important limitation:

The dataset does not contain `user_id`.

The data therefore cannot be directly joined to the User Behavior
dataset as real user-level Spotify data.

---

## 3.2 Spotify User Behavior

File:

`data/raw/spotify_user_behavior.csv`

Approximate size:

8,000 rows.

Columns:

- user_id
- gender
- age
- country
- subscription_type
- listening_time
- songs_played_per_day
- skip_rate
- device_type
- ads_listened_per_week
- offline_listening
- is_churned

This is the primary user-level behavioral dataset.

`user_id` is the master user identifier for the project.

Important business / ML variables include:

- subscription_type
- listening_time
- songs_played_per_day
- skip_rate
- device_type
- ads_listened_per_week
- offline_listening
- is_churned

---

## 3.3 Spotify User Preferences

File:

`data/raw/spotify_user_preferences.xlsx`

Approximate size:

520 rows.

Columns:

- Age
- Gender
- spotify_usage_period
- spotify_listening_device
- spotify_subscription_plan
- premium_sub_willingness
- preferred_premium_plan
- preferred_listening_content
- fav_music_genre
- music_time_slot
- music_Influencial_mood
- music_lis_frequency
- music_expl_method
- music_recc_rating
- pod_lis_frequency
- fav_pod_genre
- preffered_pod_format
- pod_host_preference
- preffered_pod_duration
- pod_variety_satisfaction

This is primarily attitudinal / preference / survey data.

It is intended to complement behavioral data.

Behavioral data answers:

"What did the user do?"

Preference data helps answer:

"What does the user prefer or want?"

Important limitation:

The preference dataset does not contain `user_id`.

Therefore preference-to-user relationships created in the project
are synthetic.

---

# 4. Data Integration Strategy

The three source datasets are not naturally relational.

The key relationships are:

User Behavior
    └── has real user_id

Streaming History
    └── no user_id

User Preferences
    └── no user_id

Therefore, the project must NOT pretend that the source datasets
originally belonged to the same users.

Any linkage between:

- streaming events
- users
- preference profiles

must be explicitly described as synthetic.

The purpose of synthetic integration is to create a realistic,
reproducible analytics environment while preserving the characteristics
of the source datasets.

---

# 5. Synthetic Data Integration Principles

Synthetic integration should NOT simply assign records randomly.

The integration engine should use meaningful constraints.

Potential signals include:

## Demographics

Use:

- age
- gender

to create more plausible preference-profile assignments.

A preference profile should ideally be mapped to a user with reasonably
similar demographic characteristics rather than purely random assignment.

---

## User Behavior

Use behavioral characteristics such as:

- listening_time
- songs_played_per_day
- skip_rate
- subscription_type
- offline_listening
- ads_listened_per_week

to influence synthetic listening behavior.

Examples:

Heavy listeners:
- more streaming events

Premium users:
- greater probability of offline listening

Free users:
- greater exposure to ad-supported sessions

High skip-rate users:
- higher probability of skipped tracks

---

## User Preferences

Use:

- fav_music_genre
- preferred_listening_content
- music_time_slot
- music_Influencial_mood
- music_lis_frequency
- music_recc_rating
- podcast preferences

to influence generated or assigned listening events.

For example, if a synthetic user preference profile indicates a
favorite genre of Rap, the user's generated listening behavior should
have a higher probability of selecting Rap-related tracks.

The mapping should remain probabilistic rather than deterministic.

For example:

Favorite genre = Rap

could result in an approximate distribution such as:

- Rap: 70%
- Hip-Hop: 15%
- Pop: 10%
- Other: 5%

The exact probabilities should be justified and documented rather than
treated as real Spotify probabilities.

---

# 6. Reproducibility

Synthetic integration must use explicit random seeds.

Running the same pipeline with the same input data and configuration
should produce reproducible results.

All important synthetic assumptions should be documented.

The project must never imply that the synthetic relationships represent
actual Spotify user relationships.

---

# 7. Raw Data Policy

Files under:

`data/raw/`

must remain unchanged.

All transformations should produce files under:

`data/processed/`

or another appropriate derived-data directory.

The raw datasets represent source data and should always remain available
for reproducibility.

---

# 8. Current Data-Cleaning Work

The project already contains:

`notebooks/01_data_understanding.ipynb`

and:

`notebooks/01_data_cleaning.ipynb`

The data-cleaning work has already established several findings.

## Streaming History

Missing values:

- reason_start: 143
- reason_end: 117

Duplicate rows:

- 1,185

Other columns had no missing values.

Cleaning performed:

- duplicate rows removed
- missing `reason_start` values replaced with `unknown`
- missing `reason_end` values replaced with `unknown`

---

## User Behavior

Findings:

- 0 missing values
- 0 duplicate rows

The dataset was considered structurally clean.

---

## User Preferences

One duplicate row was identified.

Missing values included:

- preferred_premium_plan: approximately 40%
- fav_pod_genre: approximately 28.46%
- pod_host_preference: approximately 27.12%
- preferred_podcast_format: approximately 26.92%
- preferred_podcast_duration: approximately 24.81%

These missing values appear to be potentially structural because not every
respondent necessarily uses or prefers podcasts or premium plans.

They should NOT automatically be imputed simply to eliminate missing
values.

Any future treatment should be based on the meaning of the variable.

---

# 9. Current Processed Tables

The following processed tables have already been created or partially
created.

## 9.1 tracks

File:

`data/processed/tracks.csv`

Purpose:

Track dimension table.

Created from unique combinations of:

- spotify_track_uri
- track_name
- artist_name
- album_name

Current approximate size:

16,597 unique tracks.

Columns:

- track_id
- spotify_track_uri
- track_name
- artist_name
- album_name

`track_id` is a generated surrogate key.

---

## 9.2 streaming_events

File:

`data/processed/streaming_events.csv`

Purpose:

Event/fact table representing listening events.

Intended columns include:

- stream_id
- track_id
- ts
- platform
- ms_played
- reason_start
- reason_end
- shuffle
- skipped

The original track-identifying columns are normalized through
`track_id`.

The final file should be verified before relying on it.

---

## 9.3 users

File:

`data/processed/users.csv`

Purpose:

User dimension.

Expected columns:

- user_id
- age
- gender
- country

Source:

User Behavior dataset.

---

## 9.4 user_behavior

File:

`data/processed/user_behavior.csv`

Purpose:

User-level behavioral/business metrics.

Expected columns:

- user_id
- subscription_type
- listening_time
- songs_played_per_day
- skip_rate
- device_type
- ads_listened_per_week
- offline_listening
- is_churned

---

## 9.5 user_preferences

`data/processed/user_preferences.csv` contains 8,000 user rows populated
from the 520 raw survey responses using a **synthetic** mapping. It does not
represent observed Spotify user-level preference data. Every row includes
the source spreadsheet row and demographic compatibility diagnostics.
Its grain is one synthetic survey-response assignment per `user_id`; the
primary key is `user_id`, which references `users.user_id`. Survey Age and
Gender are used only to calculate matching diagnostics and are not copied as
user demographics.

The mapper gives each observed response an expansion quota of 15 or 16 users
(8,000 total), preserving source preference-category distributions within
rounding error. It then globally maximizes age-band and normalized-gender
compatibility without hard constraints. Survey age ranges use inclusive
endpoints as written; `Others` is normalized to behavior gender `Other`.
Seeded tie-breaking makes the assignment reproducible. The exact duplicate
survey response is retained in the 520-response distribution.

No other behavioral matching is used: the survey's device responses are
multi-select, listening-frequency responses describe contexts rather than
play counts, and other fields lack defensible behavior counterparts. Missing
survey preference values remain missing.

The relationship from `user_id` to a survey response is synthetic. Never
interpret preference-to-behavior associations from this table as real user
relationships. See `docs/DATA_PIPELINE.md` for commands, validation, and
distribution comparisons.

---

# 10. Target Data Architecture

The intended architecture is:

Raw Data
   ↓
Processed Data
   ↓
Analytics Layer
   ↓
SQL / ML / Dashboard

Core analytical tables:

### Dimension / entity tables

- users
- tracks
- user_preferences

### Fact / behavioral tables

- streaming_events
- user_behavior

`user_preferences.user_id` is a synthetic linkage only. `streaming_events`
remains unlinked to users because its source has no user identifier.

### Derived analytical tables

Potential future tables include:

- daily_user_metrics
- retention_metrics
- recommendation_metrics
- churn_features

These derived tables should only be created when they support an actual
analytics requirement.

Avoid creating tables simply because a traditional warehouse might have
them.

---

# 11. SQL Analytics Goals

SQL should demonstrate practical analytical skills.

Expected concepts include:

- SELECT / filtering
- joins
- aggregations
- GROUP BY
- CASE statements
- CTEs
- window functions
- ranking
- cohort analysis
- retention analysis
- churn analysis
- engagement analysis
- funnel analysis

Potential metrics include:

- active users
- listening hours
- songs per day
- skip rate
- churn rate
- retention rate
- premium adoption
- offline usage
- recommendation engagement
- device/platform usage

SQL should answer business questions rather than exist as isolated
syntax demonstrations.

---

# 12. Exploratory Data Analysis

EDA should be hypothesis-driven.

Possible areas:

## User Engagement

- listening time
- songs played per day
- listening frequency
- platform/device behavior

## Subscription

- free vs premium behavior
- premium adoption
- premium willingness

## Churn

Potential hypotheses:

- higher skip rate may be associated with higher churn
- lower engagement may be associated with higher churn
- offline listening may be associated with retention

These are hypotheses only.

The analysis must determine whether the data supports them.

## Preferences

Explore relationships between:

- favorite genres
- listening times
- moods
- recommendation ratings
- listening frequency
- podcast preferences

---

# 13. Machine Learning

The primary ML problem is:

## Churn Prediction

Target:

`is_churned`

Potential models:

- Logistic Regression
- Random Forest
- XGBoost

The project should not automatically use every model.

Start with a simple interpretable baseline and then evaluate whether a
more complex model provides meaningful improvement.

Important evaluation metrics may include:

- precision
- recall
- F1-score
- ROC-AUC
- confusion matrix

Feature importance and explainability should be included where useful.

SHAP may be considered if it adds meaningful value.

---

# 14. User Segmentation

Use clustering to identify meaningful user groups.

A likely approach is:

K-Means clustering.

Potential features:

- listening time
- songs per day
- skip rate
- offline listening
- ads listened per week
- subscription behavior

Clusters should be interpreted from their characteristics.

Do not assign arbitrary names to clusters before analyzing their actual
behavior.

---

# 15. Experimentation

The project should demonstrate product experimentation concepts.

Potential components:

- hypothesis formulation
- control vs treatment
- A/B test analysis
- statistical significance
- confidence intervals
- effect size
- experiment design
- opportunity sizing

If real experiment data is unavailable, experiments may be simulated.

Any simulated experiment must be clearly labeled as simulated.

The project must never present simulated results as actual Spotify
experiments.

---

# 16. Recommendation Analytics

The project is NOT intended to become a highly complex recommendation
engine.

The focus should instead be on recommendation/product analytics.

Potential areas:

- recommendation rating
- recommendation acceptance
- skip behavior
- preference alignment
- recommendation satisfaction

A recommendation-related ML model may be considered as a stretch goal,
but it should not compromise the core project.

---

# 17. Streamlit Dashboard

The final project should include an interactive Streamlit dashboard.

A potential structure is:

## Page 1 — Executive Overview

Metrics such as:

- active users
- listening hours
- churn rate
- premium rate
- skip rate

## Page 2 — User Engagement

Explore:

- listening trends
- songs played
- platform/device usage
- user cohorts

## Page 3 — Churn & Segmentation

Show:

- churn distribution
- churn risk
- user clusters
- model insights
- feature importance

## Page 4 — Product Insights

Show:

- preferences
- recommendation behavior
- premium willingness
- experiment results
- product opportunities

The exact dashboard structure can change if analysis shows a better
information architecture.

---

# 18. Product Insight Philosophy

The final project should not stop at:

"Users who do X have Y."

The goal is to translate analytical findings into potential product
implications.

For example:

Observed pattern
    ↓
Possible explanation
    ↓
Business impact
    ↓
Potential product intervention
    ↓
Metric to monitor

Product recommendations must be grounded in the analysis.

---

# 19. Scope Control

This is a student portfolio project and should remain feasible.

Prioritize:

1. Clean data architecture
2. Meaningful synthetic integration
3. Strong SQL analytics
4. Strong EDA
5. Churn prediction
6. User segmentation
7. Experimentation
8. Streamlit dashboard
9. Clear documentation

Avoid unnecessary complexity such as:

- production-scale distributed systems
- microservices
- complex cloud infrastructure
- overly sophisticated recommendation engines
- dozens of ML models
- excessive feature engineering without business purpose

---

# 20. Portfolio Objective

The final project should demonstrate that the developer can move from:

Raw Data
    ↓
Data Engineering
    ↓
SQL
    ↓
Analysis
    ↓
Machine Learning
    ↓
Experimentation
    ↓
Product Insight
    ↓
Interactive Dashboard

The project should be understandable to a recruiter or interviewer
without requiring them to inspect every notebook.

The implementation should therefore prioritize:

- clean repository structure
- readable code
- reproducibility
- documented assumptions
- strong analytical reasoning
- meaningful visualizations
- practical business interpretation
