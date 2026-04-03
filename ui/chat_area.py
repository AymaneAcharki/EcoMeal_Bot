import streamlit as st
from typing import Dict, List
from .recipe_card import render_recipe_card
from .shopping_list import render_shopping_list
from chat.engine import ChatEngine
from chat.conversation_manager import ConversationManager

# Quick-select ingredient options organized by category
QUICK_INGREDIENTS = {
    "Proteins": ["Chicken", "Beef", "Pork", "Fish", "Shrimp", "Eggs", "Tofu", "Lentils", "Chickpeas", "Beans"],
    "Vegetables": ["Tomatoes", "Onions", "Garlic", "Potatoes", "Carrots", "Broccoli", "Spinach", "Peppers", "Mushrooms", "Zucchini"],
    "Carbs": ["Rice", "Pasta", "Bread", "Quinoa", "Potatoes", "Oats", "Flour", "Couscous"],
    "Dairy": ["Cheese", "Milk", "Butter", "Yogurt", "Cream", "Coconut milk"],
    "Fruits": ["Lemon", "Lime", "Apple", "Banana", "Avocado", "Berries", "Orange"],
    "Pantry": ["Olive oil", "Soy sauce", "Sugar", "Honey", "Flour", "Cornstarch", "Tomato paste"],
}

APPLIANCE_OPTIONS = ["Stovetop", "Oven", "Microwave", "Air fryer", "Blender", "Grill", "Slow cooker", "Rice cooker"]
CUISINE_OPTIONS = ["Italian", "French", "Chinese", "Japanese", "Thai", "Indian", "Mexican", "Mediterranean", "American", "African", "Middle Eastern", "Korean"]
DIFFICULTY_OPTIONS = ["Easy", "Medium", "Advanced"]


def render_chat_area() -> None:
    _ensure_conversation()
    _render_profile_toggle()
    _render_focus_toggles()
    _render_ingredient_selector()
    _render_demo_button()
    _render_message_history()
    # Note: chat_input is now in app.py (must be outside tabs)


def _ensure_conversation() -> None:
    if not st.session_state.get("active_conversation_id"):
        cm = ConversationManager()
        new_conv = cm.create_new()
        st.session_state["active_conversation_id"] = new_conv["id"]
        st.session_state["active_conversation_title"] = new_conv["title"]
        st.session_state["active_conversation_created"] = new_conv["created_at"]


def _render_profile_toggle() -> None:
    """Toggle to enable/disable profile-based personalization."""
    profile = st.session_state.get("profile")

    col_toggle, col_info = st.columns([1, 4])

    with col_toggle:
        use_profile = st.toggle(
            "Import Profile",
            value=st.session_state.get("use_profile", True),
            key="toggle_use_profile",
            help="Use your profile settings (diet, allergies, budget, country) to personalize recipes"
        )
        st.session_state["use_profile"] = use_profile

    with col_info:
        if profile and use_profile:
            diet = profile.diet_type
            country = profile.country
            budget = profile.weekly_budget
            st.markdown(
                f'<span style="color:var(--primary); font-size:0.85rem;">'
                f'Profile active: {diet.title()} | {country} | {budget:.0f} {profile.currency}/week'
                f'</span>',
                unsafe_allow_html=True
            )
        elif not use_profile:
            st.markdown(
                '<span style="color:var(--text-muted); font-size:0.85rem;">'
                'Profile disabled - recipes will use default settings'
                '</span>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<span style="color:var(--warning); font-size:0.85rem;">'
                'No profile loaded - go to Profile tab to create one'
                '</span>',
                unsafe_allow_html=True
            )


def _render_focus_toggles() -> None:
    """Render the focus mode toggles: CO2, Nutri, Eco."""
    st.markdown("#### Focus Mode")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        co2_on = st.toggle(
            "CO2",
            value=st.session_state.get("focus_co2", True),
            key="toggle_co2",
            help="Optimize for lowest carbon footprint"
        )
        if co2_on != st.session_state.get("focus_co2", True):
            st.session_state["focus_co2"] = co2_on
            _sync_focus_mode()

    with col2:
        nutri_on = st.toggle(
            "Nutri",
            value=st.session_state.get("focus_nutri", False),
            key="toggle_nutri",
            help="Optimize for nutritional value (protein, fiber, vitamins)"
        )
        if nutri_on != st.session_state.get("focus_nutri", False):
            st.session_state["focus_nutri"] = nutri_on
            _sync_focus_mode()

    with col3:
        eco_on = st.toggle(
            "Economic",
            value=st.session_state.get("focus_eco", False),
            key="toggle_eco",
            help="Optimize for budget-friendly ingredients"
        )
        if eco_on != st.session_state.get("focus_eco", False):
            st.session_state["focus_eco"] = eco_on
            _sync_focus_mode()

    # Pure Search toggle - disables all profile pre-rules
    st.markdown("---")
    pure_search = st.toggle(
        "Pure Search",
        value=st.session_state.get("pure_search", False),
        key="toggle_pure_search",
        help="Disable profile preferences (cuisine, diet) - search based only on your text input"
    )
    if pure_search != st.session_state.get("pure_search", False):
        st.session_state["pure_search"] = pure_search

    if pure_search:
        st.caption("Results from ALL cuisines, no profile filters")


def _sync_focus_mode() -> None:
    """Determine active focus mode from toggles (priority: nutri > eco > co2)."""
    if st.session_state.get("focus_nutri", False):
        st.session_state["focus_mode"] = "nutri"
    elif st.session_state.get("focus_eco", False):
        st.session_state["focus_mode"] = "eco"
    else:
        st.session_state["focus_mode"] = "co2"


def _render_ingredient_selector() -> None:
    """Render the combined ingredient selector: quick picks + text input + preferences."""
    # Fridge Waste Reducing toggle - controls whether ingredients are used
    fridge_waste = st.toggle(
        "Fridge Waste Reducing",
        value=st.session_state.get("fridge_waste_mode", False),
        key="toggle_fridge_waste",
        help="When ON: Use selected ingredients to reduce food waste. When OFF: Chat-driven search, prefer emblematic recipes."
    )
    st.session_state["fridge_waste_mode"] = fridge_waste

    if fridge_waste:
        st.caption("Ingredients will be used to find matching recipes")
        with st.expander("Your Ingredients & Preferences", expanded=True):
            _render_quick_ingredients()
            st.markdown("---")
            _render_pantry_input()
            st.markdown("---")
            _render_cooking_preferences()
    else:
        st.caption("Chat-driven mode - tell me what you want, I'll suggest emblematic recipes")


def _render_quick_ingredients() -> None:
    """Quick-select common ingredients by category."""
    st.markdown("**Quick Select Ingredients**")

    for category, items in QUICK_INGREDIENTS.items():
        st.markdown(f'<div style="margin-bottom:0.2rem; font-weight:600; color:var(--primary); font-size:0.85rem;">{category}</div>', unsafe_allow_html=True)

        selected_key = f"quick_{category.lower()}"
        current = st.session_state.get(selected_key, [])

        selected = st.multiselect(
            category,
            options=items,
            default=current,
            key=selected_key,
            label_visibility="collapsed"
        )

        if selected:
            chips = " ".join([f'<span class="ingredient-chip">{i}</span>' for i in selected])
            st.markdown(chips, unsafe_allow_html=True)


def _render_pantry_input() -> None:
    """Free-text pantry input for ingredients not in quick select."""
    st.markdown("**Other Ingredients**")
    pantry_text = st.text_area(
        "Type additional ingredients (comma-separated)",
        placeholder="e.g. fresh basil, coconut cream, cashews...",
        height=68,
        key="pantry_input",
        label_visibility="collapsed"
    )
    if pantry_text:
        items = [item.strip() for item in pantry_text.split(",") if item.strip()]
        chips = " ".join([f'<span class="ingredient-chip">{i}</span>' for i in items])
        st.markdown(chips, unsafe_allow_html=True)


def _render_cooking_preferences() -> None:
    """Appliance, cuisine, and difficulty selectors."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Appliances**")
        appliances = st.multiselect(
            "Available appliances",
            options=APPLIANCE_OPTIONS,
            default=st.session_state.get("selected_appliances", ["Stovetop"]),
            key="selected_appliances",
            label_visibility="collapsed"
        )

    with col2:
        st.markdown("**Cuisine**")
        cuisine = st.selectbox(
            "Cuisine type",
            options=["Any"] + CUISINE_OPTIONS,
            index=0,
            key="selected_cuisine",
            label_visibility="collapsed"
        )

    with col3:
        st.markdown("**Difficulty**")
        difficulty = st.selectbox(
            "Difficulty level",
            options=["Any"] + DIFFICULTY_OPTIONS,
            index=0,
            key="selected_difficulty",
            label_visibility="collapsed"
        )

    with col1:
        st.markdown("**Dish Type**")
        dish_type = st.selectbox(
            "Dish type",
            options=["Any", "Stew", "Soup", "Salad", "Curry", "Pasta", "Rice", "Sandwich", "Pizza", "Stir-fry", "Roast", "Grilled", "Fried"],
            index=0,
            key="selected_dish_type",
            label_visibility="collapsed"
        )


def _get_all_selected_ingredients() -> List[str]:
    """Combine quick-select and text input ingredients."""
    ingredients = []
    for category, items in QUICK_INGREDIENTS.items():
        selected_key = f"quick_{category.lower()}"
        selected = st.session_state.get(selected_key, [])
        ingredients.extend(selected)

    pantry_text = st.session_state.get("pantry_input", "")
    if pantry_text:
        extra = [item.strip() for item in pantry_text.split(",") if item.strip()]
        ingredients.extend(extra)

    return ingredients


def _render_message_history() -> None:
    messages = st.session_state.get("messages", [])

    if not messages:
        _render_welcome()
        return

    for msg in messages:
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        msg_type = msg.get("type", "text")
        data = msg.get("data", None)

        with st.chat_message(role):
            st.markdown(content)

            if msg_type == "recipe" and data:
                render_recipe_card(data)

            if msg_type == "shopping_list" and data:
                render_shopping_list(data)


def _render_welcome() -> None:
    st.markdown("""
    <div class="eco-card" style="text-align: center; padding: 2rem;">
        <h2>Welcome to EcoMeal Bot!</h2>
        <p style="color: var(--text-secondary); font-size: 1.05rem; margin-bottom: 1.5rem;">
            Select your ingredients above, choose your focus mode, then ask away!
        </p>
        <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 0.75rem;">
            <span class="ingredient-chip">"Suggest a recipe with chicken and rice"</span>
            <span class="ingredient-chip">"I want a vegetarian recipe"</span>
            <span class="ingredient-chip">"Make me a shopping list"</span>
            <span class="ingredient-chip">"Plan my meals for the week"</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_demo_button() -> None:
    """Render the Run Demo button that showcases bot capabilities."""
    messages = st.session_state.get("messages", [])
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button(
            "Run Demo" if not messages else "Re-run Demo",
            type="primary" if not messages else "secondary",
            help="Run a scripted demo: Spaghetti Bolognese -> Vegetarian Pesto -> Indian Chicken Curry",
            use_container_width=True
        ):
            _run_demo()


def _run_demo() -> None:
    """Execute scripted demo conversation with optimal recipe results."""
    # Clear previous messages
    st.session_state["messages"] = []

    engine = st.session_state.get("chat_engine")
    if not engine:
        st.session_state["messages"].append({
            "role": "assistant",
            "content": "Chat engine not available. Please check your setup.",
            "type": "text",
            "data": None
        })
        st.rerun()
        return

    # Demo scenario with specific recipe IDs to force
    demo_steps = [
        {
            "user": "I want a spaghetti bolognese recipe",
            "recipe_id": 44959,  # Beef Polenta with Spaghetti
            "bot_msg": "Here's a recipe for you: **{name}**",
        },
        {
            "user": "make it vegetarian",
            "recipe_id": 14934,  # Saltimbocca with Crushed Tomatoes & Garlic (vegetarian penne)
            "bot_msg": "Here's an alternative: **{name}**",
        },
        {
            "user": "now suggest an indian dish",
            "recipe_id": 38045,  # Chicken Thighs Curry with Rice
            "bot_msg": "Here's a recipe for you: **{name}**",
        },
    ]

    for step in demo_steps:
        # Add user message
        st.session_state["messages"].append({
            "role": "user",
            "content": step["user"],
            "type": "text",
            "data": None
        })

        # Track carbon for this request
        start_time = engine.carbon_tracker.start_call()

        # Get the specific recipe from DB
        recipe_raw = None
        if engine.recipe_search:
            recipe_raw = engine.recipe_search.get_recipe_by_id(step["recipe_id"])

        if recipe_raw:
            formatted = engine.recipe_search.format_recipe_for_display(recipe_raw, engine.profile)
            formatted['source'] = 'database'
            formatted['database_id'] = recipe_raw.get('id')
            engine.history.set_current_recipe(formatted)

            # Record carbon
            import time
            engine.carbon_tracker.end_call(start_time, tokens_generated=0, call_type="demo")

            msg = step["bot_msg"].format(name=formatted["name"])
            st.session_state["messages"].append({
                "role": "assistant",
                "content": msg,
                "type": "recipe",
                "data": formatted
            })
        else:
            # Fallback: use normal engine processing
            engine.carbon_tracker.end_call(start_time, tokens_generated=0, call_type="demo_fallback")
            response = engine.process_message(step["user"], [])
            msg_type = response.get("type", "text")
            data = None
            if msg_type == "recipe":
                data = response.get("recipe")
            st.session_state["messages"].append({
                "role": "assistant",
                "content": response.get("message", ""),
                "type": msg_type,
                "data": data
            })

    # Persist carbon data
    st.session_state["carbon_summary"] = engine.carbon_tracker.get_session_summary()

    # Update stats
    _update_conversation_stats()
    st.session_state["active_conversation_title"] = "Demo - Spaghetti, Pesto, Curry"

    # Archive
    cm = ConversationManager()
    conversation = {
        "id": st.session_state["active_conversation_id"],
        "title": st.session_state.get("active_conversation_title", "Demo"),
        "messages": st.session_state["messages"],
        "stats": st.session_state["session_stats"],
        "created_at": st.session_state.get("active_conversation_created", ""),
        "updated_at": ""
    }
    cm.archive(conversation)

    st.rerun()


def _render_chat_input() -> None:
    """Deprecated - chat_input moved to app.py for HF Spaces compatibility."""
    pass


def handle_user_input(user_input: str) -> None:
    """Handle user input from chat_input in app.py."""
    pantry_items = _get_all_selected_ingredients()
    _process_user_message(user_input, pantry_items)


def _ensure_engine_matches_profile_toggle() -> None:
    """Rebuild chat engine if profile toggle state changed."""
    use_profile = st.session_state.get("use_profile", True)
    prev_state = st.session_state.get("_prev_use_profile", True)

    if use_profile != prev_state:
        from profile.models import UserProfile
        if use_profile:
            profile = st.session_state.get("profile") or UserProfile(user_id="default_user")
        else:
            profile = UserProfile(user_id="default_user")

        try:
            st.session_state["chat_engine"] = ChatEngine(profile)
        except Exception:
            st.session_state["chat_engine"] = None
        st.session_state["_prev_use_profile"] = use_profile


def _process_user_message(user_text: str, pantry_items: List[str]) -> None:
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Build constraints from UI selections
    constraints = _build_constraints()

    # Fridge Waste Reducing mode: only use pantry items when toggle is ON
    fridge_waste_mode = st.session_state.get("fridge_waste_mode", False)
    if not fridge_waste_mode:
        pantry_items = []  # Ignore pantry - rely on chat only
        constraints["prefer_emblematic"] = True  # Flag to prefer emblematic recipes
    else:
        constraints["prefer_emblematic"] = False

    st.session_state["messages"].append({
        "role": "user",
        "content": user_text,
        "type": "text",
        "data": None
    })

    # Rebuild engine with/without profile based on toggle
    _ensure_engine_matches_profile_toggle()

    chat_engine = st.session_state.get("chat_engine")

    if not chat_engine:
        st.session_state["messages"].append({
            "role": "assistant",
            "content": "Chat engine not initialized. Please check your profile settings or LM Studio connection.",
            "type": "text",
            "data": None
        })
        st.rerun()
        return

    with st.spinner("Thinking..."):
        response = chat_engine.process_message(
            user_text,
            pantry_items,
            constraints=constraints
        )

    # Persist carbon tracker data for Analysis tab
    if hasattr(chat_engine, "carbon_tracker"):
        st.session_state["carbon_summary"] = chat_engine.carbon_tracker.get_session_summary()

    msg_type = response.get("type", "text")
    message = response.get("message", "")

    data = None
    if msg_type == "recipe":
        data = response.get("recipe")
    elif msg_type == "shopping_list":
        data = response.get("shopping_list")
    elif msg_type == "weekly_plan":
        data = response.get("weekly_plan")

    st.session_state["messages"].append({
        "role": "assistant",
        "content": message,
        "type": msg_type,
        "data": data
    })

    _update_conversation_stats()
    _update_conversation_title()

    cm = ConversationManager()
    conversation = {
        "id": st.session_state["active_conversation_id"],
        "title": st.session_state.get("active_conversation_title", "New Conversation"),
        "messages": st.session_state["messages"],
        "stats": st.session_state["session_stats"],
        "created_at": st.session_state.get("active_conversation_created", ""),
        "updated_at": ""
    }
    cm.archive(conversation)

    st.rerun()


def _build_constraints() -> Dict:
    """Build constraints dict from UI selections and optionally profile."""
    constraints = {}

    # Pure Search mode - disables profile preferences
    pure_search = st.session_state.get("pure_search", False)
    constraints["pure_search"] = pure_search

    appliances = st.session_state.get("selected_appliances", [])
    if appliances:
        constraints["appliances"] = appliances

    # Cuisine filter only if not in pure search mode
    if not pure_search:
        cuisine = st.session_state.get("selected_cuisine", "Any")
        if cuisine != "Any":
            constraints["cuisine"] = cuisine

    difficulty = st.session_state.get("selected_difficulty", "Any")
    if difficulty != "Any":
        constraints["difficulty"] = difficulty.lower()

    # Dish type filter
    dish_type = st.session_state.get("selected_dish_type", "Any")
    if dish_type != "Any":
        constraints["dish_type"] = dish_type.lower().replace("-", "_")

    # Focus mode
    focus_mode = st.session_state.get("focus_mode", "co2")
    constraints["focus_mode"] = focus_mode

    # Profile-based constraints (only when toggle is ON and NOT pure search)
    if st.session_state.get("use_profile", True) and not pure_search:
        profile = st.session_state.get("profile")
        if profile:
            if profile.diet_type and profile.diet_type != "omnivore":
                constraints["diet"] = profile.diet_type
            if profile.allergies:
                constraints["allergies"] = profile.allergies  # Always include allergies for safety
            if profile.max_cooking_time and profile.max_cooking_time != 60:
                constraints["max_time"] = profile.max_cooking_time
            if profile.skill_level and profile.skill_level != "beginner":
                constraints["skill"] = profile.skill_level

    # Always include allergies for safety, even in pure search
    if pure_search:
        profile = st.session_state.get("profile")
        if profile and profile.allergies:
            constraints["allergies"] = profile.allergies

    return constraints


def _update_conversation_stats() -> None:
    messages = st.session_state.get("messages", [])
    cm = ConversationManager()
    st.session_state["session_stats"] = cm.compute_stats(messages)


def _update_conversation_title() -> None:
    current = st.session_state.get("active_conversation_title", "New Conversation")
    if current != "New Conversation":
        return

    messages = st.session_state.get("messages", [])
    if messages:
        cm = ConversationManager()
        title = cm.auto_title(messages)
        st.session_state["active_conversation_title"] = title
