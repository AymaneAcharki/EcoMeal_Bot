import streamlit as st
from typing import Dict
from .styles import render_co2_badge, render_ingredient_chip, render_step


def render_recipe_card(recipe: Dict) -> None:
    name = recipe.get('name', 'Unnamed Recipe')
    description = recipe.get('description', '')
    ingredients = recipe.get('ingredients', [])
    steps = recipe.get('steps', [])
    cooking_time = recipe.get('cooking_time_minutes', 30)
    difficulty = recipe.get('difficulty', 'medium')
    sustainability_tip = recipe.get('sustainability_tip', '')
    co2_info = recipe.get('co2_info', {})
    co2_label = recipe.get('co2_label', {})
    comparison = recipe.get('comparison', {})
    substitutions = recipe.get('substitutions', [])
    
    st.markdown(f"""
    <div class="eco-card">
        <h3>{name}</h3>
        <p style="color: var(--text-muted); margin-bottom: 1rem;">{description}</p>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Cooking Time", f"{cooking_time} min")
    with col2:
        difficulty_colors = {'easy': '🟢', 'medium': '🟡', 'advanced': '🔴'}
        emoji = difficulty_colors.get(difficulty, '⚪')
        st.metric("Difficulty", f"{emoji} {difficulty.title()}")
    with col3:
        total_co2 = co2_info.get('total_co2_kg', 0)
        badge_html = render_co2_badge(total_co2, co2_label)
        st.markdown(f"**CO2 Impact**<br>{badge_html}", unsafe_allow_html=True)
    
    if comparison:
        status = comparison.get('status', 'unknown')
        diff_kg = comparison.get('difference_kg', 0)
        pct = comparison.get('percentage', 0)
        
        if status == 'below':
            st.success(f"🌱 {abs(pct):.1f}% below average French meal ({abs(diff_kg):.2f} kg CO2 saved)")
        else:
            st.warning(f"📈 {pct:.1f}% above average French meal (+{diff_kg:.2f} kg CO2)")
    
    st.markdown("---")
    
    st.markdown("#### 🥗 Ingredients")
    ingredient_chips = []
    for ing in ingredients:
        ing_name = ing.get('name', 'Unknown')
        qty = ing.get('quantity_g')
        chip = render_ingredient_chip(ing_name, qty)
        ingredient_chips.append(chip)
    
    st.markdown(' '.join(ingredient_chips), unsafe_allow_html=True)
    
    if co2_info.get('breakdown'):
        st.markdown("##### CO2 Breakdown")
        breakdown_html = "<div style='font-size: 0.85rem;'>"
        for item in co2_info.get('breakdown', []):
            breakdown_html += f"<div class='shopping-item'><span>{item.get('name')}</span><span class='price-tag'>{item.get('co2_kg', 0):.3f} kg</span></div>"
        breakdown_html += "</div>"
        st.markdown(breakdown_html, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("#### 📝 Instructions")
    
    for i, step in enumerate(steps, 1):
        st.markdown(render_step(i, step), unsafe_allow_html=True)
    
    if sustainability_tip:
        st.info(f"💡 **Sustainability Tip:** {sustainability_tip}")
    
    if substitutions:
        st.markdown("---")
        st.markdown("#### 🔄 Suggested Substitutions")
        
        for sub in substitutions:
            original = sub.get('original', '')
            original_co2 = sub.get('original_co2', 0)
            substitutes = sub.get('substitutes', [])
            savings = sub.get('potential_savings', 0)
            
            if original and substitutes:
                st.markdown(f"""
                <div class="substitution-card">
                    <strong>{original}</strong> ({original_co2:.1f} kg CO2/kg)<br>
                    → Try: <strong>{', '.join(substitutes)}</strong><br>
                    <small>Potential savings: {savings:.1f} kg CO2/kg</small>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_recipe_compact(recipe: Dict) -> str:
    name = recipe.get('name', 'Unnamed Recipe')
    cooking_time = recipe.get('cooking_time_minutes', 30)
    difficulty = recipe.get('difficulty', 'medium')
    co2_info = recipe.get('co2_info', {})
    total_co2 = co2_info.get('total_co2_kg', 0)
    
    return f"""
    <div class="eco-card" style="padding: 1rem;">
        <strong>{name}</strong><br>
        <small>⏱ {cooking_time} min | 📊 {difficulty} | 🌍 {total_co2:.2f} kg CO2</small>
    </div>
    """


def render_recipe_list_html(recipes: list) -> str:
    html = "<div style='display: flex; flex-wrap: wrap; gap: 1rem;'>"
    for recipe in recipes:
        html += render_recipe_compact(recipe)
    html += "</div>"
    return html
