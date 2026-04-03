import streamlit as st
from profile.manager import ProfileManager
from chat.conversation_manager import ConversationManager
import config


def render_sidebar() -> None:
    with st.sidebar:
        _render_header()
        st.markdown("---")
        _render_conversation_controls()
        st.markdown("---")
        _render_lm_status()
        st.markdown("---")
        _render_profile_switch()
        st.markdown("---")
        _render_session_stats()
        st.markdown("---")
        _render_actions()


def _render_header() -> None:
    st.markdown(f"""
    <div class="sidebar-logo">
        <h2>EcoMeal Bot</h2>
        <small>v{config.APP_VERSION}</small>
    </div>
    """, unsafe_allow_html=True)


def _render_conversation_controls() -> None:
    st.markdown("**Conversation**")

    active_title = st.session_state.get("active_conversation_title", "New Conversation")
    st.markdown(f'<div class="conversation-active">{active_title}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("New Chat", use_container_width=True):
            _save_current_conversation()
            _start_new_conversation()

    with col2:
        if st.button("History", use_container_width=True):
            st.session_state["show_history"] = not st.session_state.get("show_history", False)
            st.rerun()

    if st.session_state.get("show_history", False):
        _render_conversation_history()


def _render_conversation_history() -> None:
    cm = ConversationManager()
    conversations = cm.list_all()

    if not conversations:
        st.caption("No conversation history yet.")
        return

    st.markdown("**Past Conversations**")

    for conv in conversations[:20]:
        col_info, col_btn = st.columns([3, 1])
        with col_info:
            title = conv.get("title", "Untitled")
            if len(title) > 35:
                title = title[:35] + "..."
            msg_count = conv.get("messages_count", 0)
            recipe_count = conv.get("recipes_count", 0)
            st.markdown(
                f'<div class="conversation-item">'
                f'<div class="conversation-item-title">{title}</div>'
                f'<div class="conversation-item-meta">{msg_count} msgs, {recipe_count} recipes</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        with col_btn:
            if st.button("Load", key=f"load_{conv['id']}", use_container_width=True):
                _load_conversation(conv["id"])

    if len(conversations) > 20:
        st.caption(f"...and {len(conversations) - 20} more")


def _save_current_conversation() -> None:
    messages = st.session_state.get("messages", [])
    if not messages:
        return

    conv_id = st.session_state.get("active_conversation_id")
    if not conv_id:
        return

    cm = ConversationManager()
    title = st.session_state.get("active_conversation_title", "New Conversation")
    if title == "New Conversation" and messages:
        title = cm.auto_title(messages)

    conversation = {
        "id": conv_id,
        "title": title,
        "messages": messages,
        "stats": cm.compute_stats(messages),
        "created_at": st.session_state.get("active_conversation_created", ""),
        "updated_at": ""
    }
    cm.archive(conversation)

    stats = cm.compute_stats(messages)
    cum = st.session_state.get("cumulative_stats", {"messages": 0, "recipes": 0})
    cum["messages"] += stats["messages"]
    cum["recipes"] += stats["recipes"]
    st.session_state["cumulative_stats"] = cum


def _start_new_conversation() -> None:
    cm = ConversationManager()
    new_conv = cm.create_new()
    st.session_state["messages"] = []
    st.session_state["active_conversation_id"] = new_conv["id"]
    st.session_state["active_conversation_title"] = new_conv["title"]
    st.session_state["active_conversation_created"] = new_conv["created_at"]
    st.session_state["session_stats"] = {"messages": 0, "recipes": 0}

    chat_engine = st.session_state.get("chat_engine")
    if chat_engine and hasattr(chat_engine, "history"):
        chat_engine.history.clear()

    st.rerun()


def _load_conversation(conv_id: str) -> None:
    _save_current_conversation()

    cm = ConversationManager()
    conv = cm.load(conv_id)
    if not conv:
        st.error("Conversation not found.")
        return

    st.session_state["messages"] = conv.get("messages", [])
    st.session_state["active_conversation_id"] = conv.get("id", conv_id)
    st.session_state["active_conversation_title"] = conv.get("title", "Untitled")
    st.session_state["active_conversation_created"] = conv.get("created_at", "")
    st.session_state["session_stats"] = conv.get("stats", {"messages": 0, "recipes": 0})
    st.session_state["show_history"] = False

    chat_engine = st.session_state.get("chat_engine")
    if chat_engine and hasattr(chat_engine, "history"):
        chat_engine.history.clear()
        for msg in conv.get("messages", []):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            chat_engine.history.add_message(role, content)

    st.rerun()


def _render_lm_status() -> None:
    lm_connected = st.session_state.get("lm_connected", False)

    if lm_connected:
        st.markdown(f"""
        <div style="padding: 0.5rem; border-radius: 8px; background-color: var(--primary-light);">
            <span class="status-dot status-dot-online"></span>
            <small style="color: var(--primary-dark); font-weight: 600;">LM Studio Connected</small>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="padding: 0.5rem; border-radius: 8px; background-color: var(--danger-light);">
            <span class="status-dot status-dot-offline"></span>
            <small style="color: var(--danger); font-weight: 600;">LM Studio Disconnected</small>
        </div>
        """, unsafe_allow_html=True)
        st.caption("Fallback mode active")

    thinking = st.toggle(
        "Thinking Mode",
        value=st.session_state.get("thinking_enabled", False),
        key="sidebar_thinking_toggle",
        help="Enable model reasoning before responding. Slower but more thorough."
    )
    if thinking != st.session_state.get("thinking_enabled", False):
        st.session_state["thinking_enabled"] = thinking
        config.LM_STUDIO_THINKING_ENABLED = thinking
        engine = st.session_state.get("chat_engine")
        if engine:
            engine.thinking_enabled = thinking

    if st.button("Test Connection", use_container_width=True):
        try:
            from chat.engine import ChatEngine
            profile = st.session_state.get("profile")
            if profile:
                engine = ChatEngine(profile)
                engine.thinking_enabled = st.session_state.get("thinking_enabled", False)
                st.session_state["chat_engine"] = engine
                st.session_state["lm_connected"] = engine.llm_available
                st.rerun()
        except Exception:
            st.session_state["lm_connected"] = False
            st.rerun()


def _render_profile_switch() -> None:
    st.markdown("**User Profile**")

    profile_manager = ProfileManager()
    profiles = profile_manager.list_profiles()
    profile_options = [p["user_id"] for p in profiles] if profiles else ["default_user"]

    current_user_id = st.session_state.get("current_user_id", "default_user")
    default_index = profile_options.index(current_user_id) if current_user_id in profile_options else 0

    selected_user = st.selectbox(
        "User",
        options=profile_options,
        index=default_index,
        key="sidebar_user_select",
        label_visibility="collapsed"
    )

    if selected_user != current_user_id:
        st.session_state["current_user_id"] = selected_user
        profile = profile_manager.load_profile(selected_user)
        st.session_state["profile"] = profile

        try:
            from chat.engine import ChatEngine
            st.session_state["chat_engine"] = ChatEngine(profile)
            st.session_state["lm_connected"] = st.session_state["chat_engine"].llm_available
        except Exception:
            st.session_state["chat_engine"] = None
            st.session_state["lm_connected"] = False
        st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("New", use_container_width=True):
            st.session_state["show_new_profile"] = True

    with col2:
        if st.button("Delete", use_container_width=True):
            if current_user_id != "default_user":
                profile_manager.delete_profile(current_user_id)
                st.session_state["current_user_id"] = "default_user"
                for k in ["profile_diet", "profile_allergies", "profile_cuisines",
                           "profile_skill", "profile_max_time", "profile_budget",
                           "profile_household", "profile_priority"]:
                    st.session_state.pop(k, None)
                st.rerun()

    if st.session_state.get("show_new_profile", False):
        new_id = st.text_input("New User ID", key="new_user_id_input")
        col_a, col_b = st.columns(2)
        with col_a:
            if new_id and st.button("Create"):
                profile_manager.create_default_profile(new_id)
                st.session_state["current_user_id"] = new_id
                st.session_state["show_new_profile"] = False
                st.rerun()
        with col_b:
            if st.button("Cancel"):
                st.session_state["show_new_profile"] = False
                st.rerun()


def _render_session_stats() -> None:
    st.markdown("**Session**")
    stats = st.session_state.get("session_stats", {"messages": 0, "recipes": 0})
    cum = st.session_state.get("cumulative_stats", {"messages": 0, "recipes": 0})

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Messages", stats.get("messages", 0))
    with col2:
        st.metric("Recipes", stats.get("recipes", 0))

    if cum["messages"] > 0:
        st.caption(f"Total archived: {cum['messages']} msgs, {cum['recipes']} recipes")


def _render_actions() -> None:
    if st.button("Clear Session", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
