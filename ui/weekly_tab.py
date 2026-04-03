import streamlit as st
from typing import Dict, List
from .styles import render_co2_badge
from .recipe_card import render_recipe_compact
import config


def render_weekly_tab() -> None:
    st.markdown("## 📅 Weekly Meal Plan")
    st.markdown("Plan your meals for the week while staying within budget and minimizing CO2.")
    
    weekly_plan = st.session_state.get("weekly_plan")
    
    if not weekly_plan:
        _render_weekly_generator()
        return
    
    _render_weekly_results(weekly_plan)


def _render_weekly_generator() -> None:
    profile = st.session_state.get("profile")
    
    st.markdown("""
    <div class="eco-card" style="text-align: center; padding: 2rem;">
        <h3>No weekly plan yet</h3>
        <p style="color: var(--text-muted);">Generate a personalized weekly meal plan based on your preferences.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        budget = st.number_input(
            "Weekly Budget (EUR)",
            min_value=20,
            max_value=500,
            value=int(profile.weekly_budget) if profile else 100,
            key="weekly_plan_budget"
        )
    
    with col2:
        household = st.number_input(
            "Household Size",
            min_value=1,
            max_value=8,
            value=profile.household_size if profile else 2,
            key="weekly_plan_household"
        )
    
    pantry_input = st.text_input(
        "🧊 Available Ingredients (comma-separated)",
        placeholder="e.g. rice, chicken, tomatoes, onions, pasta...",
        key="weekly_plan_pantry"
    )
    
    if st.button("Generate Weekly Plan", use_container_width=True, type="primary"):
        pantry_items = [item.strip() for item in pantry_input.split(",") if item.strip()]

        chat_engine = st.session_state.get("chat_engine")
        if chat_engine:
            with st.spinner("Generating your weekly meal plan..."):
                constraints = {
                    "weekly_budget": budget,
                    "household_size": household,
                    "focus_mode": st.session_state.get("focus_mode", "co2")
                }
                response = chat_engine._handle_weekly_plan(pantry_items, constraints)
                st.session_state["weekly_plan"] = response.get("weekly_plan", {})
                st.rerun()
        else:
            st.error("Chat engine not initialized.")
    
    if st.button("🔄 Reset Weekly Plan"):
        st.session_state["weekly_plan"] = None
        st.rerun()


def _render_weekly_results(weekly_plan: Dict) -> None:
    days = weekly_plan.get("days", [])
    total_cost = weekly_plan.get("total_estimated_cost", 0)
    total_co2 = weekly_plan.get("total_estimated_co2", 0)
    
    if not days:
        st.warning("No meals in the weekly plan. Try generating a new one.")
        if st.button("🔄 Try Again"):
            st.session_state["weekly_plan"] = None
            st.rerun()
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Days Planned", f"{len(days)} / 7")
    with col2:
        st.metric("Est. Total Cost", f"{total_cost:.2f} EUR")
    with col3:
        co2_label = _get_co2_category(total_co2 / max(len(days), 1))
        st.metric("Avg CO2 / Meal", f"{total_co2 / max(len(days), 1):.2f} kg")
    
    st.markdown("---")
    
    for day_entry in days:
        day_name = day_entry.get("day", "Unknown")
        meal = day_entry.get("meal", "No meal planned")
        ingredients = day_entry.get("ingredients", [])
        
        with st.expander(f"📅 {day_name} - {meal}", expanded=False):
            if ingredients:
                ingredient_chips = " ".join(
                    [f'<span class="ingredient-chip">{ing}</span>' for ing in ingredients]
                )
                st.markdown(f"**Ingredients:** {ingredient_chips}", unsafe_allow_html=True)
            else:
                st.info("No ingredients listed for this meal.")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="eco-card" style="text-align: center;">
            <h4>💰 Cost Summary</h4>
            <p style="font-size: 1.5rem; color: var(--primary);">{total_cost:.2f} EUR</p>
            <small style="color: var(--text-muted);">per week</small>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="eco-card" style="text-align: center;">
            <h4>🌍 CO2 Summary</h4>
            <p style="font-size: 1.5rem; color: var(--primary);">{total_co2:.2f} kg</p>
            <small style="color: var(--text-muted);">total estimated</small>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("🔄 Generate New Plan"):
        st.session_state["weekly_plan"] = None
        st.rerun()


def _get_co2_category(avg_co2: float) -> str:
    if avg_co2 <= 0.5:
        return "Excellent"
    elif avg_co2 <= 1.5:
        return "Low"
    elif avg_co2 <= 3.0:
        return "Medium"
    elif avg_co2 <= 5.0:
        return "High"
    return "Very High"
