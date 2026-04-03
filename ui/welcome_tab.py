import socket
import io
import base64
import os

import qrcode
import streamlit as st
import config


def _is_cloud_deployment() -> bool:
    """Check if running on Hugging Face Spaces or other cloud."""
    return bool(os.environ.get("HF_API_TOKEN") and os.environ.get("SPACE_ID"))


def render_welcome_tab() -> None:
    _render_hero()
    # Skip QR code section on cloud deployment (HF Spaces has its own URL)
    if not _is_cloud_deployment():
        _render_access_section()
    _render_features()
    _render_how_it_works()
    _render_key_numbers()


def _render_hero() -> None:
    st.markdown("""
    <div class="hero-section">
        <h1>EcoMeal Bot</h1>
        <p class="hero-subtitle">Your Sustainable Cooking Assistant</p>
        <p class="hero-tagline">UN SDG 12 - Responsible Consumption</p>
    </div>
    """, unsafe_allow_html=True)


def _get_local_url() -> str:
    """Get the local network URL for this Streamlit app."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "127.0.0.1"
    port = 8501
    return f"http://{ip}:{port}"


def _generate_qr_base64(url: str) -> str:
    """Generate a QR code as base64 PNG string."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def _render_access_section() -> None:
    """Render QR code + local network link for spectators."""
    local_url = _get_local_url()
    qr_b64 = _generate_qr_base64(local_url)

    st.markdown("### Access From Your Phone")
    st.markdown("Scan the QR code or open the link below to use EcoMeal Bot on your device.")

    col_qr, col_info = st.columns([1, 2])

    with col_qr:
        st.markdown(
            f'<img src="data:image/png;base64,{qr_b64}" '
            f'alt="QR Code" style="width: 200px; border-radius: 12px; '
            f'box-shadow: 0 2px 12px rgba(0,0,0,0.1);" />',
            unsafe_allow_html=True
        )

    with col_info:
        st.markdown(
            f'<div style="display:flex; flex-direction:column; gap:1rem; padding-top:0.5rem;">'
            f'<div style="font-size:1.3rem; font-weight:700; color:var(--primary);">'
            f'{local_url}</div>'
            f'<p style="color:var(--text-secondary); font-size:0.95rem;">'
            f'Make sure your device is connected to the same WiFi network as this computer.'
            f'</p>'
            f'</div>',
            unsafe_allow_html=True
        )

        if st.button("Copy Link", use_container_width=True):
            import pyperclip
            pyperclip.copy(local_url)
            st.toast("Link copied!")


def _render_features() -> None:
    st.markdown("### What We Offer")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🥗</div>
            <h4>Eco Recipes</h4>
            <p>Generate personalized recipes based on your ingredients, with minimal CO2 impact.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🌍</div>
            <h4>CO2 Tracking</h4>
            <p>Calculate the carbon footprint of every meal and compare it to the French average.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📅</div>
            <h4>Meal Planning</h4>
            <p>Plan your weekly meals within budget with smart shopping lists.</p>
        </div>
        """, unsafe_allow_html=True)


def _render_how_it_works() -> None:
    st.markdown("### How It Works")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="step-card">
            <div class="step-icon">1</div>
            <h4>Tell us your ingredients</h4>
            <p>List the ingredients you have in your kitchen.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="step-card">
            <div class="step-icon">2</div>
            <h4>Personalized recipe</h4>
            <p>Our AI creates a recipe tailored to your tastes and dietary needs.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="step-card">
            <div class="step-icon">3</div>
            <h4>Eat sustainably</h4>
            <p>Track your environmental impact and improve your eating habits.</p>
        </div>
        """, unsafe_allow_html=True)


def _render_key_numbers() -> None:
    st.markdown("### Key Numbers")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="metric-box">
            <div class="metric-value">2.5</div>
            <div class="metric-label">kg CO2 / avg meal (FR)</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-box">
            <div class="metric-value">27</div>
            <div class="metric-label">kg CO2 / kg of beef</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-box">
            <div class="metric-value">97%</div>
            <div class="metric-label">CO2 reduction with lentils</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="metric-box">
            <div class="metric-value">30%</div>
            <div class="metric-label">less waste with planning</div>
        </div>
        """, unsafe_allow_html=True)
