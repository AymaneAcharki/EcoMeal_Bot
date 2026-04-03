import streamlit as st
from typing import Dict, List
import config


def render_stats_tab() -> None:
    st.markdown("## 📊 Sustainability Dashboard")
    st.markdown("Track your environmental impact and cooking progress.")
    
    chat_engine = st.session_state.get("chat_engine")
    
    if not chat_engine:
        st.warning("Start chatting to see your stats!")
        return
    
    stats = chat_engine.get_history_stats()
    recipes_history = chat_engine.history.recipes_history
    
    if not recipes_history:
        st.info("Generate some recipes to see your sustainability stats.")
        _render_tips_section()
        return
    
    _render_overview_stats(stats, recipes_history)
    _render_co2_breakdown(recipes_history)
    _render_recipe_history(recipes_history)
    _render_tips_section()


def _render_overview_stats(stats: Dict, recipes_history: List[Dict]) -> None:
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
        <div class="stat-card">
            <h2>{total_co2:.1f}</h2>
            <p>Total CO2 (kg)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <h2>{avg_co2:.2f}</h2>
            <p>Avg CO2 / Meal (kg)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        score_color = "#27ae60" if sustainability_score >= 70 else "#f39c12" if sustainability_score >= 40 else "#e74c3c"
        st.markdown(f"""
        <div class="stat-card" style="background: linear-gradient(135deg, {score_color} 0%, {score_color}dd 100%);">
            <h2>{sustainability_score}</h2>
            <p>Eco Score / 100</p>
        </div>
        """, unsafe_allow_html=True)


def _render_co2_breakdown(recipes_history: List[Dict]) -> None:
    st.markdown("### 🌍 CO2 Impact by Recipe")
    
    co2_data = []
    for entry in recipes_history:
        recipe = entry.get("recipe", {})
        name = recipe.get("name", "Unknown")
        co2 = recipe.get("co2_info", {}).get("total_co2_kg", 0)
        label_info = recipe.get("co2_label", {})
        label = label_info.get("label", "N/A")
        co2_data.append({
            "name": name,
            "co2_kg": co2,
            "label": label
        })
    
    if co2_data:
        rows_html = ""
        for i, item in enumerate(co2_data, 1):
            bar_width = min(100, (item["co2_kg"] / 6.0) * 100)
            
            if item["co2_kg"] <= 0.5:
                bar_color = "#27ae60"
            elif item["co2_kg"] <= 1.5:
                bar_color = "#2ecc71"
            elif item["co2_kg"] <= 3.0:
                bar_color = "#f39c12"
            elif item["co2_kg"] <= 5.0:
                bar_color = "#e67e22"
            else:
                bar_color = "#e74c3c"
            
            rows_html += f"""
            <div style="margin-bottom: 0.75rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                    <small><strong>{i}. {item['name']}</strong></small>
                    <small>{item['co2_kg']:.2f} kg CO2 ({item['label']})</small>
                </div>
                <div style="background-color: var(--bg-secondary); border-radius: 4px; overflow: hidden;">
                    <div style="width: {bar_width}%; background-color: {bar_color}; height: 8px;"></div>
                </div>
            </div>
            """
        
        st.markdown(f'<div class="eco-card">{rows_html}</div>', unsafe_allow_html=True)
    
    avg_co2 = sum(d["co2_kg"] for d in co2_data) / len(co2_data) if co2_data else 0
    
    col1, col2 = st.columns(2)
    with col1:
        if avg_co2 <= config.FRENCH_AVG_CO2_PER_MEAL:
            st.success(f"🌱 Your average ({avg_co2:.2f} kg) is below the French average ({config.FRENCH_AVG_CO2_PER_MEAL} kg/meal)")
        else:
            st.warning(f"📈 Your average ({avg_co2:.2f} kg) is above the French average ({config.FRENCH_AVG_CO2_PER_MEAL} kg/meal)")
    
    with col2:
        savings = max(0, config.FRENCH_AVG_CO2_PER_MEAL - avg_co2) * len(co2_data)
        st.info(f"💡 Estimated CO2 savings: {savings:.2f} kg across {len(co2_data)} meals")


def _render_recipe_history(recipes_history: List[Dict]) -> None:
    st.markdown("### 📝 Recipe History")
    
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


def _render_tips_section() -> None:
    st.markdown("### 💡 Eco Tips")
    
    tips = [
        ("🥩 Reduce Red Meat", "Beef produces 27 kg CO2/kg. Replace with lentils (0.9 kg CO2/kg) to cut emissions by 97%."),
        ("🥬 Eat Seasonal", "Seasonal produce has lower transport emissions and tastes better. Check the seasonal availability guide."),
        ("📦 Plan Your Meals", "Weekly meal planning reduces food waste by up to 30%. Use our weekly planner to get started."),
        ("🍲 Batch Cook", "Cooking larger portions and freezing leftovers saves energy and reduces waste."),
        ("🛒 Smart Shopping", "Buy only what you need. Use our shopping list to avoid over-purchasing.")
    ]
    
    for title, description in tips:
        st.markdown(f"""
        <div class="eco-card" style="padding: 1rem;">
            <strong>{title}</strong><br>
            <small style="color: var(--text-muted);">{description}</small>
        </div>
        """, unsafe_allow_html=True)
