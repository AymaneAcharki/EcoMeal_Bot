import streamlit as st
import config
from chat.engine import ChatEngine
from profile.manager import ProfileManager
from ui.sidebar import render_sidebar
from ui.chat_area import render_chat_area, handle_user_input
from ui.welcome_tab import render_welcome_tab
from ui.profile_tab import render_profile_tab
from ui.analysis_tab import render_analysis_tab
from ui.styles import load_css


st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    if "initialized" not in st.session_state:
        st.session_state["initialized"] = True
        st.session_state["messages"] = []
        st.session_state["session_stats"] = {"messages": 0, "recipes": 0}
        st.session_state["cumulative_stats"] = {"messages": 0, "recipes": 0}
        st.session_state["lm_connected"] = False
        st.session_state["weekly_plan"] = None
        st.session_state["current_user_id"] = "default_user"
        st.session_state["show_new_profile"] = False
        st.session_state["active_conversation_id"] = None
        st.session_state["active_conversation_title"] = "New Conversation"
        st.session_state["current_tab"] = 1  # 0=Home, 1=Chat, 2=Profile, 3=Analysis

    if "profile" not in st.session_state:
        pm = ProfileManager()
        user_id = st.session_state.get("current_user_id", "default_user")
        st.session_state["profile"] = pm.load_profile(user_id)

    if "chat_engine" not in st.session_state:
        profile = st.session_state.get("profile")
        if profile:
            try:
                st.session_state["chat_engine"] = ChatEngine(profile)
                st.session_state["lm_connected"] = True
            except Exception:
                st.session_state["chat_engine"] = None
                st.session_state["lm_connected"] = False


def render_main_content():
    tabs = st.tabs(["🏠 Home", "💬 Chat", "👤 Profile", "📊 Analysis"])

    # Track which tab is selected via query params or default
    current_tab = st.session_state.get("current_tab", 1)

    with tabs[0]:
        render_welcome_tab()

    with tabs[1]:
        render_chat_area()

    with tabs[2]:
        render_profile_tab()

    with tabs[3]:
        render_analysis_tab()

    # Chat input at app level (required by Streamlit - must be outside tabs)
    # But only process when user is on Chat tab
    user_input = st.chat_input(
        "Ask for a recipe, shopping list, weekly plan...",
        key="chat_input_global"
    )

    if user_input:
        handle_user_input(user_input)


def render_footer():
    provider_name = "Hugging Face" if config.LLM_PROVIDER == "huggingface" else "LM Studio"
    st.markdown("---")
    st.markdown(f"""
    <div class="footer">
        {config.APP_TITLE} v{config.APP_VERSION} |
        UN SDG 12: Responsible Consumption |
        Powered by {provider_name}
    </div>
    """, unsafe_allow_html=True)


def main():
    init_session_state()
    load_css()
    render_sidebar()
    render_main_content()
    render_footer()


if __name__ == "__main__":
    main()
