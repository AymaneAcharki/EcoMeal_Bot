import streamlit as st
from typing import Dict, List


def render_shopping_list(shopping_data: Dict) -> None:
    if not shopping_data:
        st.warning("No shopping list data available.")
        return
    
    missing_items = shopping_data.get("missing_items", [])
    total_cost = shopping_data.get("total_cost", 0)
    currency = shopping_data.get("currency", "EUR")
    items_with_cost = shopping_data.get("items_with_cost", [])
    seasonal_notes = shopping_data.get("seasonal_notes", [])
    over_budget = shopping_data.get("over_budget", False)
    
    if not missing_items:
        st.success("✅ You already have everything you need!")
        return
    
    st.markdown(f"""
    <div class="eco-card">
        <h3>🛒 Shopping List</h3>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.metric("Items to Buy", len(missing_items))
    with col2:
        st.metric(f"Total Cost", f"{total_cost:.2f} {currency}")
    
    if over_budget:
        budget = shopping_data.get("budget", 0)
        excess = shopping_data.get("excess", 0)
        st.error(f"⚠️ Over budget by {excess:.2f} {currency} (budget: {budget:.2f} {currency})")
    
    st.markdown("---")
    
    st.markdown("#### Items")
    
    items_html = "<div style='margin-top: 0.5rem;'>"
    
    for item in items_with_cost:
        name = item.get("name", "Unknown")
        quantity_g = item.get("quantity_g", 100)
        price_per_kg = item.get("price_per_kg", 0)
        cost = item.get("cost", 0)
        
        items_html += f"""
        <div class="shopping-item">
            <span>
                <strong>{name}</strong>
                <small style="color: var(--text-muted);"> ({quantity_g}g)</small>
            </span>
            <span class="price-tag">{cost:.2f} {currency}</span>
        </div>
        """
    
    items_html += f"""
    <div class="shopping-item" style="border-top: 2px solid var(--primary); padding-top: 0.75rem; margin-top: 0.5rem;">
        <span><strong>Total</strong></span>
        <span class="price-tag" style="font-size: 1.1rem;">{total_cost:.2f} {currency}</span>
    </div>
    """
    items_html += "</div>"
    
    st.markdown(items_html, unsafe_allow_html=True)
    
    if seasonal_notes:
        st.markdown("---")
        st.markdown("#### 🌿 Seasonal Notes")
        
        for note in seasonal_notes:
            item_name = note.get("item", "")
            status = note.get("status", "")
            message = note.get("note", "")
            
            if status == "peak_season":
                st.success(f"🌟 **{item_name}**: {message}")
            elif status == "out_of_season":
                st.warning(f"⚠️ **{item_name}**: {message}")
            elif status == "imported":
                st.info(f"✈️ **{item_name}**: {message}")
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_shopping_list_compact(shopping_data: Dict) -> str:
    if not shopping_data:
        return ""
    
    items = shopping_data.get("missing_items", [])
    total = shopping_data.get("total_cost", 0)
    currency = shopping_data.get("currency", "EUR")
    
    html = f"""
    <div class="eco-card" style="padding: 1rem;">
        <strong>🛒 Shopping List</strong> - {len(items)} items<br>
        <small>Total: <span class="price-tag">{total:.2f} {currency}</span></small>
    </div>
    """
    return html
