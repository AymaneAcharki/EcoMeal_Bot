import streamlit as st
import config
from chat.engine import ChatEngine
from profile.manager import ProfileManager
from ui.sidebar import render_sidebar
from ui.chat_area import render_chat_area
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
    tab_home, tab_chat, tab_profile, tab_analysis = st.tabs([
        "Home",
        "Chat",
        "Profile",
        "Analysis"
    ])

    # Track active tab in session state
    if "active_tab" not in st.session_state:
        st.session_state["active_tab"] = "Chat"

    with tab_home:
        st.session_state["active_tab"] = "Home"
        render_welcome_tab()

    with tab_chat:
        st.session_state["active_tab"] = "Chat"
        render_chat_area()

    with tab_profile:
        st.session_state["active_tab"] = "Profile"
        render_profile_tab()

    with tab_analysis:
        st.session_state["active_tab"] = "Analysis"
        render_analysis_tab()

    # Chat input MUST be outside tabs - show when Chat tab is contextually active
    user_input = st.chat_input(
        "Ask for a recipe, shopping list, weekly plan...",
        key="chat_input_main"
    )

    if user_input and st.session_state.get("active_tab") == "Chat":
        from ui.chat_area import handle_user_input
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
