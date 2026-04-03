import streamlit as st
from typing import Dict, List
import matplotlib.pyplot as plt
import config
from profile.manager import ProfileManager
from profile.defaults import CHOICES


def render_profile_tab() -> None:
    _render_profile_settings()
    st.markdown("---")
    _render_dashboard()


def _render_profile_settings() -> None:
    st.markdown("""
    <div class="profile-section">
        <h3>Profile Settings</h3>
    </div>
    """, unsafe_allow_html=True)

    profile = st.session_state.get("profile")
    if not profile:
        st.warning("No profile loaded.")
        return

    pm = ProfileManager()

    with st.form("profile_form"):
        col1, col2 = st.columns(2)

        with col1:
            country_keys = list(CHOICES["countries"].keys())
            country = st.selectbox(
                "Country",
                options=country_keys,
                index=country_keys.index(profile.country) if profile.country in country_keys else 0,
                format_func=lambda x: CHOICES["countries"].get(x, x),
                help="Used to calculate realistic CO2 emissions based on your region"
            )

            diet_keys = list(CHOICES["diet_type"].keys())
            diet = st.selectbox(
                "Diet Type",
                options=diet_keys,
                index=diet_keys.index(profile.diet_type) if profile.diet_type in diet_keys else 0,
                format_func=lambda x: CHOICES["diet_type"].get(x, x)
            )

            allergy_keys = list(CHOICES["allergies"].keys())
            current_allergies = [a for a in profile.allergies if a in allergy_keys]
            allergies = st.multiselect(
                "Allergies",
                options=allergy_keys,
                default=current_allergies,
                format_func=lambda x: CHOICES["allergies"].get(x, x)
            )

            cuisine_keys = list(CHOICES["cuisine_preferences"].keys())
            current_cuisines = [c for c in profile.cuisine_preferences if c in cuisine_keys]
            cuisines = st.multiselect(
                "Cuisine Preferences",
                options=cuisine_keys,
                default=current_cuisines,
                format_func=lambda x: CHOICES["cuisine_preferences"].get(x, x)
            )

        with col2:
            skill_keys = list(CHOICES["skill_level"].keys())
            skill = st.select_slider(
                "Cooking Skill",
                options=skill_keys,
                value=profile.skill_level if profile.skill_level in skill_keys else skill_keys[0],
                format_func=lambda x: CHOICES["skill_level"].get(x, x)
            )

            max_time = st.slider(
                "Max Cooking Time (min)",
                min_value=15,
                max_value=120,
                value=profile.max_cooking_time
            )

            col_budget, col_household = st.columns(2)
            with col_budget:
                budget = st.number_input(
                    "Weekly Budget (EUR)",
                    min_value=10,
                    max_value=500,
                    value=int(profile.weekly_budget)
                )
            with col_household:
                household = st.number_input(
                    "Household Size",
                    min_value=1,
                    max_value=8,
                    value=profile.household_size
                )

            priority_keys = list(CHOICES["sustainability_priority"].keys())
            priority = st.radio(
                "Sustainability Priority",
                options=priority_keys,
                index=priority_keys.index(profile.sustainability_priority) if profile.sustainability_priority in priority_keys else 0,
                format_func=lambda x: CHOICES["sustainability_priority"].get(x, x),
                horizontal=True
            )

        st.markdown("---")
        submitted = st.form_submit_button("Save Profile", use_container_width=True, type="primary")

    if submitted:
        profile.update(
            country=country,
            diet_type=diet,
            allergies=allergies,
            cuisine_preferences=cuisines,
            skill_level=skill,
            max_cooking_time=max_time,
            weekly_budget=float(budget),
            household_size=household,
            sustainability_priority=priority
        )
        pm.save_profile(profile)
        st.session_state["profile"] = profile
        st.success("Profile saved!")


def _render_dashboard() -> None:
    st.markdown("### Dashboard")

    chat_engine = st.session_state.get("chat_engine")

    if not chat_engine:
        st.info("Start chatting to see your stats here!")
        return

    stats = chat_engine.get_history_stats()
    recipes_history = chat_engine.history.recipes_history

    if not recipes_history:
        st.info("Generate some recipes to see your sustainability stats.")
        _render_tips()
        return

    _render_overview_metrics(stats, recipes_history)
    _render_co2_chart(recipes_history)
    _render_budget_chart(recipes_history)
    _render_eco_score(recipes_history)
    _render_recipe_history(recipes_history)
    _render_tips()


def _render_overview_metrics(stats: Dict, recipes_history: List[Dict]) -> None:
    total_co2 = sum(
        r.get("recipe", {}).get("co2_info", {}).get("total_co2_kg", 0)
        for r in recipes_history
    )
    avg_co2 = total_co2 / len(recipes_history) if recipes_history else 0

    meals_below_avg = sum(
        1 for r in recipes_history
        if r.get("recipe", {}).get("comparison", {}).get("status") == "below"
    )

    sustainability_score = min(100, int((meals_below_avg / max(len(recipes_history), 1)) * 100))

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <h2>{len(recipes_history)}</h2>
            <p>Recipes Generated</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card" style="background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);">
            <h2>{total_co2:.1f}</h2>
            <p>Total CO2 (kg)</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stat-card" style="background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);">
            <h2>{avg_co2:.2f}</h2>
            <p>Avg CO2 / Meal (kg)</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        score_color = "#27ae60" if sustainability_score >= 70 else "#FF9800" if sustainability_score >= 40 else "#E53935"
        st.markdown(f"""
        <div class="stat-card" style="background: linear-gradient(135deg, {score_color} 0%, {score_color}dd 100%);">
            <h2>{sustainability_score}</h2>
            <p>Eco Score / 100</p>
        </div>
        """, unsafe_allow_html=True)


def _render_co2_chart(recipes_history: List[Dict]) -> None:
    st.markdown("#### CO2 Evolution by Meal")

    co2_values = []
    names = []
    for entry in recipes_history:
        recipe = entry.get("recipe", {})
        name = recipe.get("name", "?")
        co2 = recipe.get("co2_info", {}).get("total_co2_kg", 0)
        short_name = name[:15] + "..." if len(name) > 15 else name
        names.append(short_name)
        co2_values.append(round(co2, 2))

    if co2_values:
        col1, col2 = st.columns([3, 1])
        with col1:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(names, co2_values, color="#2e7d32")
            ax.set_xlabel("Meal")
            ax.set_ylabel("CO2 (kg)")
            ax.set_title("CO2 by Meal")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        with col2:
            avg = sum(co2_values) / len(co2_values)
            if avg <= config.FRENCH_AVG_CO2_PER_MEAL:
                st.success(f"Avg: {avg:.2f} kg\nBelow French avg ({config.FRENCH_AVG_CO2_PER_MEAL} kg)")
            else:
                st.warning(f"Avg: {avg:.2f} kg\nAbove French avg ({config.FRENCH_AVG_CO2_PER_MEAL} kg)")

            savings = max(0, config.FRENCH_AVG_CO2_PER_MEAL - avg) * len(co2_values)
            st.metric("Estimated CO2 Savings", f"{savings:.2f} kg")


def _render_budget_chart(recipes_history: List[Dict]) -> None:
    st.markdown("#### Budget Tracking")

    total_estimated = sum(
        r.get("recipe", {}).get("co2_info", {}).get("total_co2_kg", 0) * 2.5
        for r in recipes_history
    )

    profile = st.session_state.get("profile")
    budget = profile.weekly_budget if profile else 100.0

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Weekly Budget", f"{budget:.0f} EUR")
        st.metric("Meals Planned", f"{len(recipes_history)}")

    with col2:
        remaining = max(0, budget - total_estimated)
        pct_used = min(100, (total_estimated / max(budget, 1)) * 100)

        st.markdown(f"""
        <div style="margin-top: 1rem;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <strong>Budget Used</strong>
                <span>{pct_used:.0f}%</span>
            </div>
            <div class="eco-progress">
                <div class="eco-progress-bar" style="width: {pct_used}%; background-color: {'var(--primary)' if pct_used < 80 else 'var(--warning)' if pct_used < 95 else 'var(--danger)'};"></div>
            </div>
            <small style="color: var(--text-muted);">Remaining: {remaining:.0f} EUR</small>
        </div>
        """, unsafe_allow_html=True)


def _render_eco_score(recipes_history: List[Dict]) -> None:
    st.markdown("#### Eco Score")

    meals_below_avg = sum(
        1 for r in recipes_history
        if r.get("recipe", {}).get("comparison", {}).get("status") == "below"
    )

    score = min(100, int((meals_below_avg / max(len(recipes_history), 1)) * 100))

    if score >= 70:
        label = "Excellent"
        color = "var(--primary)"
        tip = "Your food choices are very sustainable! Keep it up."
    elif score >= 40:
        label = "Average"
        color = "var(--warning)"
        tip = "Try replacing red meat with plant-based alternatives."
    else:
        label = "Needs Improvement"
        color = "var(--danger)"
        tip = "Focus on low CO2 recipes and seasonal ingredients."

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem; font-weight: 800; color: {color};">{score}</div>
            <div style="font-size: 1.2rem; font-weight: 600; color: {color};">{label}</div>
            <div style="color: var(--text-muted); font-size: 0.85rem;">/ 100</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="margin-top: 1rem;">
            <div class="eco-progress" style="height: 20px;">
                <div class="eco-progress-bar" style="width: {score}%; background-color: {color};"></div>
            </div>
            <p style="margin-top: 1rem; color: var(--text-secondary);">{tip}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-box">
                <div class="metric-value">{meals_below_avg}</div>
                <div class="metric-label">Meals Below Avg</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{len(recipes_history) - meals_below_avg}</div>
                <div class="metric-label">Meals Above Avg</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_recipe_history(recipes_history: List[Dict]) -> None:
    st.markdown("#### Recipe History")

    for i, entry in enumerate(reversed(recipes_history[-10:]), 1):
        recipe = entry.get("recipe", {})
        name = recipe.get("name", "Unknown")
        co2 = recipe.get("co2_info", {}).get("total_co2_kg", 0)
        timestamp = entry.get("timestamp", "")
        difficulty = recipe.get("difficulty", "N/A")
        cooking_time = recipe.get("cooking_time_minutes", "N/A")

        with st.expander(f"{i}. {name} ({co2:.2f} kg CO2)", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("CO2", f"{co2:.2f} kg")
            with col2:
                st.metric("Time", f"{cooking_time} min")
            with col3:
                st.metric("Difficulty", difficulty.title())

            if timestamp:
                st.caption(f"Generated: {timestamp}")


def _render_tips() -> None:
    st.markdown("#### Eco Tips")

    tips = [
        ("Reduce Red Meat", "Beef produces 27 kg CO2/kg. Replace with lentils (0.9 kg CO2/kg) to cut emissions by 97%."),
        ("Eat Seasonal", "Seasonal produce has lower transport emissions and tastes better."),
        ("Plan Your Meals", "Weekly meal planning reduces food waste by up to 30%."),
        ("Batch Cook", "Cook larger portions and freeze leftovers to save energy and reduce waste."),
    ]

    cols = st.columns(2)
    for i, (title, desc) in enumerate(tips):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="eco-card" style="padding: 1rem;">
                <strong>{title}</strong><br>
                <small style="color: var(--text-muted);">{desc}</small>
            </div>
            """, unsafe_allow_html=True)
