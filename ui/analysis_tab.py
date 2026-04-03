import streamlit as st
import config
from core.carbon_tracker import CarbonTracker, GPT4_EMISSIONS_PER_REQUEST_G


def render_analysis_tab() -> None:
    _render_sdg_table()
    st.markdown("---")
    _render_carbon_dashboard()
    st.markdown("---")
    _render_ethics()
    st.markdown("---")
    _render_key_points()
    st.markdown("---")
    _render_workflow()


def _render_sdg_table() -> None:
    st.markdown("""
    <div class="profile-section">
        <h3>UN Sustainable Development Goals Alignment</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        "How EcoMeal Bot contributes to the United Nations 2030 Agenda for Sustainable Development."
    )

    sdgs = [
        {
            "goal": "SDG 2",
            "title": "Zero Hunger",
            "icon": "02",
            "color": "#DDA63A",
            "relevance": "Direct",
            "description": "Promotes sustainable nutrition by helping users plan balanced meals "
                           "within budget, reducing food insecurity through smarter shopping and "
                           "portion planning.",
            "features": [
                "Budget-aware meal planning (weekly budget tracker)",
                "Household size consideration for portions",
                "Nutritional focus mode (Nutri toggle)",
            ],
        },
        {
            "goal": "SDG 3",
            "title": "Good Health and Well-being",
            "icon": "03",
            "color": "#4C9F38",
            "relevance": "Direct",
            "description": "Encourages healthier eating habits through dietary preference support "
                           "(vegetarian, vegan, flexitarian) and ingredient substitution suggestions "
                           "that improve both health and sustainability.",
            "features": [
                "Diet type profiles (omnivore to vegan)",
                "Allergy-aware recipe filtering",
                "Healthier ingredient substitution engine",
            ],
        },
        {
            "goal": "SDG 4",
            "title": "Quality Education",
            "icon": "04",
            "color": "#C5192D",
            "relevance": "Indirect",
            "description": "Educates users about the environmental impact of their food choices "
                           "through real-time CO2 calculations, comparison to national averages, and "
                           "sustainability tips on every recipe.",
            "features": [
                "Real-time CO2 calculation per ingredient",
                "Country-specific average comparison (52 countries)",
                "Sustainability tips on every recipe card",
            ],
        },
        {
            "goal": "SDG 12",
            "title": "Responsible Consumption and Production",
            "icon": "12",
            "color": "#BF8B2E",
            "relevance": "Primary",
            "description": "Core mission of EcoMeal Bot. Tracks CO2 emissions per meal, suggests "
                           "eco-friendly ingredient swaps, generates optimized shopping lists to reduce "
                           "over-purchasing, and promotes seasonal eating.",
            "features": [
                "CO2 badge on every recipe (Excellent to Very High)",
                "Eco-friendly substitution suggestions with % reduction",
                "Shopping list with budget and category filters",
                "Seasonal ingredient data",
                "52-country CO2 multiplier system",
            ],
        },
        {
            "goal": "SDG 13",
            "title": "Climate Action",
            "icon": "13",
            "color": "#3F7E44",
            "relevance": "Direct",
            "description": "Gives individuals actionable data on their food carbon footprint. "
                           "Each recipe shows kg CO2 emitted, comparison to the national average, and "
                           "concrete steps to reduce emissions through ingredient swaps.",
            "features": [
                "CO2 tracking dashboard with evolution chart",
                "Eco Score (0-100) based on meal history",
                "Country-adjusted CO2 multipliers (Our World in Data)",
                "Weekly CO2 budget tracking",
            ],
        },
    ]

    for sdg in sdgs:
        badge_color = (
            "var(--primary)" if sdg["relevance"] == "Primary"
            else "#2196F3" if sdg["relevance"] == "Direct"
            else "#FF9800"
        )

        st.markdown(f"""
        <div style="
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-left: 5px solid {sdg['color']};
            border-radius: var(--radius);
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: var(--shadow);
        ">
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem;">
                <div style="
                    background: {sdg['color']};
                    color: white;
                    width: 56px;
                    height: 56px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: 800;
                    font-size: 1.1rem;
                    flex-shrink: 0;
                ">
                    {sdg['icon']}
                </div>
                <div style="flex: 1;">
                    <div style="font-size: 1.15rem; font-weight: 700; color: var(--text);">
                        {sdg['title']}
                    </div>
                    <span style="
                        background: {badge_color}22;
                        color: {badge_color};
                        padding: 2px 10px;
                        border-radius: 12px;
                        font-size: 0.78rem;
                        font-weight: 600;
                    ">
                        {sdg['relevance']} Alignment
                    </span>
                </div>
            </div>
            <p style="color: var(--text-secondary); margin: 0 0 0.75rem 0; font-size: 0.92rem; line-height: 1.5;">
                {sdg['description']}
            </p>
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                {" ".join(f'<span style="background: var(--bg-hover); color: var(--text-secondary); padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; border: 1px solid var(--border-light);">{f}</span>' for f in sdg['features'])}
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_carbon_dashboard() -> None:
    """Render Code Carbon-style emissions dashboard."""
    st.markdown("""
    <div class="profile-section">
        <h3>Environmental Impact - Carbon Tracker</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        "Real-time tracking of CO2 emissions from LLM inference. "
        "Measures energy consumption from GPU/CPU/RAM during each request "
        "and calculates carbon footprint based on your country's grid intensity."
    )

    # Get tracker data: prefer session_state cache, then live engine
    summary = st.session_state.get("carbon_summary")
    if not summary:
        engine = st.session_state.get("chat_engine")
        tracker = getattr(engine, "carbon_tracker", None) if engine else None
        if tracker:
            summary = tracker.get_session_summary()
        else:
            country_obj = st.session_state.get("profile", None)
            c_name = getattr(country_obj, "country", "France") if country_obj else "France"
            demo_tracker = CarbonTracker(country=c_name)
            summary = demo_tracker.get_session_summary()

    total_co2_kg = summary["total_co2_kg"]
    total_co2_g = summary["total_co2_g"]
    total_energy_kwh = summary["total_energy_kwh"]
    avg_duration_s = summary["avg_duration_s"]
    avg_co2_per_call_g = summary["avg_co2_per_call_g"]
    total_calls = summary["total_calls"]
    gpt4_comparison = summary["gpt4_comparison"]
    hardware = summary["hardware"]
    grid = summary["grid"]
    session_duration_s = summary["session_duration_s"]

    # Format session duration
    if session_duration_s >= 3600:
        session_str = f"{session_duration_s / 3600:.1f} h"
    elif session_duration_s >= 60:
        session_str = f"{session_duration_s / 60:.1f} min"
    else:
        session_str = f"{session_duration_s:.0f} sec"

    # === 4 Metric Cards ===
    col1, col2, col3, col4 = st.columns(4)

    # Card 1: Total emissions
    with col1:
        co2_display = f"{total_co2_g:.4f}" if total_co2_kg < 0.001 else f"{total_co2_kg:.6f}"
        unit = "g" if total_co2_kg < 0.001 else "kg"
        co2_val = total_co2_g if total_co2_kg < 0.001 else total_co2_kg
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border: 1px solid #0f3460;
            border-radius: 12px;
            padding: 1.25rem;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        ">
            <div style="color: #e94560; font-size: 0.7rem; text-transform: uppercase;
                        letter-spacing: 1px; font-weight: 600; margin-bottom: 0.5rem;">
                Total Emissions
            </div>
            <div style="color: #ffffff; font-size: 1.6rem; font-weight: 800;
                        font-family: 'Courier New', monospace;">
                {co2_val:.4f}
            </div>
            <div style="color: #a0a0c0; font-size: 0.78rem; margin-top: 0.25rem;">
                {unit} CO2eq per session
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Card 2: Energy consumed
    with col2:
        energy_display = f"{total_energy_kwh * 1000:.4f}" if total_energy_kwh < 0.001 else f"{total_energy_kwh:.8f}"
        energy_unit = "Wh" if total_energy_kwh < 0.001 else "kWh"
        energy_val = total_energy_kwh * 1000 if total_energy_kwh < 0.001 else total_energy_kwh
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border: 1px solid #0f3460;
            border-radius: 12px;
            padding: 1.25rem;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        ">
            <div style="color: #e9b44c; font-size: 0.7rem; text-transform: uppercase;
                        letter-spacing: 1px; font-weight: 600; margin-bottom: 0.5rem;">
                Energy Consumed
            </div>
            <div style="color: #ffffff; font-size: 1.6rem; font-weight: 800;
                        font-family: 'Courier New', monospace;">
                {energy_val:.4f}
            </div>
            <div style="color: #a0a0c0; font-size: 0.78rem; margin-top: 0.25rem;">
                {energy_unit} per inference run
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Card 3: Avg runtime
    with col3:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border: 1px solid #0f3460;
            border-radius: 12px;
            padding: 1.25rem;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        ">
            <div style="color: #50b8e7; font-size: 0.7rem; text-transform: uppercase;
                        letter-spacing: 1px; font-weight: 600; margin-bottom: 0.5rem;">
                Avg. Runtime
            </div>
            <div style="color: #ffffff; font-size: 1.6rem; font-weight: 800;
                        font-family: 'Courier New', monospace;">
                {avg_duration_s:.2f}
            </div>
            <div style="color: #a0a0c0; font-size: 0.78rem; margin-top: 0.25rem;">
                sec per user request
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Card 4: Emissions per request vs GPT-4
    with col4:
        savings = gpt4_comparison["savings_pct"]
        savings_color = "#27ae60" if savings > 90 else "#f39c12" if savings > 50 else "#e74c3c"
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border: 1px solid #0f3460;
            border-radius: 12px;
            padding: 1.25rem;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        ">
            <div style="color: #27ae60; font-size: 0.7rem; text-transform: uppercase;
                        letter-spacing: 1px; font-weight: 600; margin-bottom: 0.5rem;">
                Per Request vs GPT-4
            </div>
            <div style="color: #ffffff; font-size: 1.6rem; font-weight: 800;
                        font-family: 'Courier New', monospace;">
                {avg_co2_per_call_g:.4f}
            </div>
            <div style="color: {savings_color}; font-size: 0.78rem; margin-top: 0.25rem;">
                g CO2eq (GPT-4: ~{GPT4_EMISSIONS_PER_REQUEST_G}g) -{savings:.0f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

    # === Infrastructure Footer ===
    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    col_left, col_mid, col_right = st.columns(3)

    with col_left:
        st.markdown(f"""
        <div style="
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: 8px;
            padding: 0.85rem 1rem;
        ">
            <div style="color: var(--text-muted); font-size: 0.72rem; text-transform: uppercase;
                        letter-spacing: 0.5px; margin-bottom: 0.4rem;">Hardware</div>
            <div style="color: var(--text); font-weight: 600; font-size: 0.88rem;">
                {hardware.get('cpu', 'CPU N/A')}
            </div>
            <div style="color: var(--text-muted); font-size: 0.78rem; margin-top: 0.2rem;">
                GPU: {hardware['gpu']}
            </div>
            <div style="color: var(--text-muted); font-size: 0.78rem;">
                GPU TDP: {hardware['gpu_tdp_w']}W |
                CPU: {hardware['cpu_tdp_w']}W |
                RAM: {hardware['ram_gb']}GB
            </div>
            <div style="color: var(--text-muted); font-size: 0.78rem;">
                Inference Power: {hardware['inference_power_w']}W
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_mid:
        st.markdown(f"""
        <div style="
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: 8px;
            padding: 0.85rem 1rem;
        ">
            <div style="color: var(--text-muted); font-size: 0.72rem; text-transform: uppercase;
                        letter-spacing: 0.5px; margin-bottom: 0.4rem;">Region / Grid</div>
            <div style="color: var(--text); font-weight: 600; font-size: 0.88rem;">
                {grid['country']}
            </div>
            <div style="color: var(--text-muted); font-size: 0.78rem; margin-top: 0.2rem;">
                Grid Intensity: {grid['intensity_gco2_kwh']} gCO2/kWh
            </div>
            <div style="color: var(--text-muted); font-size: 0.78rem;">
                Source: IEA 2023, Ember Climate
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown(f"""
        <div style="
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: 8px;
            padding: 0.85rem 1rem;
        ">
            <div style="color: var(--text-muted); font-size: 0.72rem; text-transform: uppercase;
                        letter-spacing: 0.5px; margin-bottom: 0.4rem;">Duration / Runs</div>
            <div style="color: var(--text); font-weight: 600; font-size: 0.88rem;">
                {total_calls} LLM calls
            </div>
            <div style="color: var(--text-muted); font-size: 0.78rem; margin-top: 0.2rem;">
                Session: {session_str}
            </div>
            <div style="color: {savings_color}; font-size: 0.78rem;">
                vs Cloud: {gpt4_comparison['savings_pct']:.0f}% less CO2
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Methodology note
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    with st.expander("Methodology"):
        st.markdown("""
        **How we calculate emissions:**

        1. **Power Measurement**: We use hardware Thermal Design Power (TDP) values.
           - GPU inference uses ~70% of TDP (not full load during generation)
           - CPU uses ~30% TDP (feeding data to GPU)
           - RAM: ~3W per 8GB

        2. **Energy**: `E (kWh) = Power (W) x Duration (s) / 3,600,000`

        3. **CO2eq**: `CO2 (g) = E (kWh) x Grid Intensity (gCO2/kWh)`

        4. **Grid Intensity**: Country-specific values from IEA 2023 and Ember Climate.
           France: 56 gCO2/kWh (mostly nuclear), World average: ~350 gCO2/kWh.

        5. **GPT-4 Comparison**: Estimated ~2.5g CO2eq per request based on
           published studies (University of Washington, Hugging Face).
           This includes datacenter PUE, cooling, and networking overhead
           that local inference avoids entirely.

        **Why local LLM is greener**: Running Qwen3.5:0.8b on consumer hardware
        avoids datacenter overhead (PUE ~1.1-1.5), network transfer emissions,
        and shared infrastructure costs. A single GPT-4 request emits as much
        as ~100+ local inference calls on a laptop.
        """)


def _render_ethics() -> None:
    st.markdown("""
    <div class="profile-section">
        <h3>Ethical Framework</h3>
    </div>
    """, unsafe_allow_html=True)

    ethics = [
        {
            "title": "Privacy & Data Sovereignty",
            "icon": "+",
            "description": "All user data (profiles, conversations, preferences) stored locally. "
                           "No external API calls. No data leaves the user's machine. "
                           "Fully offline-capable architecture.",
        },
        {
            "title": "Transparency & Scientific Rigor",
            "icon": "~",
            "description": "CO2 data sourced from ADEME (Agence de la Transition Ecologique), "
                           "Our World in Data, FAO, and Poore & Nemecek (2018, Science). "
                           "All thresholds and multipliers are documented and verifiable.",
        },
        {
            "title": "Accessibility & Inclusivity",
            "icon": "=",
            "description": "Free and open-source. Works offline without internet. "
                           "Supports 52 countries with localized CO2 averages. "
                           "Diet-inclusive (omnivore to vegan, allergy-aware). "
                           "Budget-adaptive for different income levels.",
        },
        {
            "title": "AI Ethics",
            "icon": "!",
            "description": "Uses a local LLM (LM Studio, Qwen3.5:0.8b) with no cloud dependency. "
                           "User controls all parameters (temperature, thinking mode). "
                           "Database-first approach: AI supplements, never replaces, factual data. "
                           "Fallback recipes available when AI is offline.",
        },
        {
            "title": "Environmental Responsibility",
            "icon": "#",
            "description": "No cloud compute needed - runs on consumer hardware. "
                           "Promotes quantifiable behavior change through CO2 tracking. "
                           "Encourages plant-based alternatives with measurable impact data. "
                           "Reduces food waste through meal planning and shopping lists.",
        },
    ]

    cols = st.columns(len(ethics))
    for col, item in zip(cols, ethics):
        with col:
            st.markdown(f"""
            <div style="
                background: var(--bg-card);
                border: 1px solid var(--border-light);
                border-radius: var(--radius);
                padding: 1.25rem;
                height: 100%;
                box-shadow: var(--shadow);
            ">
                <div style="
                    width: 42px; height: 42px;
                    background: var(--primary-light);
                    color: var(--primary);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.2rem;
                    font-weight: 800;
                    margin-bottom: 0.75rem;
                ">{item['icon'][0]}</div>
                <div style="font-weight: 700; color: var(--text); margin-bottom: 0.5rem; font-size: 0.95rem;">
                    {item['title']}
                </div>
                <p style="color: var(--text-muted); font-size: 0.82rem; line-height: 1.5; margin: 0;">
                    {item['description']}
                </p>
            </div>
            """, unsafe_allow_html=True)


def _render_key_points() -> None:
    st.markdown("""
    <div class="profile-section">
        <h3>Key Model Features</h3>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("""
        <div style="
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: var(--radius);
            padding: 1.25rem;
            box-shadow: var(--shadow);
        ">
            <h4 style="color: var(--primary); margin-bottom: 1rem;">Data & Knowledge</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                <tr style="border-bottom: 1px solid var(--border-light);">
                    <td style="padding: 0.5rem 0; color: var(--text-muted);">Recipe Database</td>
                    <td style="padding: 0.5rem 0; font-weight: 600; text-align: right;">2,000 real recipes</td>
                </tr>
                <tr style="border-bottom: 1px solid var(--border-light);">
                    <td style="padding: 0.5rem 0; color: var(--text-muted);">Cuisines Covered</td>
                    <td style="padding: 0.5rem 0; font-weight: 600; text-align: right;">20 world cuisines</td>
                </tr>
                <tr style="border-bottom: 1px solid var(--border-light);">
                    <td style="padding: 0.5rem 0; color: var(--text-muted);">Food Items (CO2 DB)</td>
                    <td style="padding: 0.5rem 0; font-weight: 600; text-align: right;">80+ foods with CO2/kg</td>
                </tr>
                <tr style="border-bottom: 1px solid var(--border-light);">
                    <td style="padding: 0.5rem 0; color: var(--text-muted);">Country Coverage</td>
                    <td style="padding: 0.5rem 0; font-weight: 600; text-align: right;">52 countries</td>
                </tr>
                <tr style="border-bottom: 1px solid var(--border-light);">
                    <td style="padding: 0.5rem 0; color: var(--text-muted);">CO2 Data Source</td>
                    <td style="padding: 0.5rem 0; font-weight: 600; text-align: right;">ADEME + Our World in Data</td>
                </tr>
                <tr style="border-bottom: 1px solid var(--border-light);">
                    <td style="padding: 0.5rem 0; color: var(--text-muted);">Price Database</td>
                    <td style="padding: 0.5rem 0; font-weight: 600; text-align: right;">EUR/kg with categories</td>
                </tr>
                <tr>
                    <td style="padding: 0.5rem 0; color: var(--text-muted);">Seasonal Data</td>
                    <td style="padding: 0.5rem 0; font-weight: 600; text-align: right;">Month-by-month availability</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <div style="
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: var(--radius);
            padding: 1.25rem;
            box-shadow: var(--shadow);
        ">
            <h4 style="color: var(--secondary); margin-bottom: 1rem;">AI & Architecture</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                <tr style="border-bottom: 1px solid var(--border-light);">
                    <td style="padding: 0.5rem 0; color: var(--text-muted);">LLM Engine</td>
                    <td style="padding: 0.5rem 0; font-weight: 600; text-align: right;">Qwen3.5:0.8b (local)</td>
                </tr>
                <tr style="border-bottom: 1px solid var(--border-light);">
                    <td style="padding: 0.5rem 0; color: var(--text-muted);">AI Platform</td>
                    <td style="padding: 0.5rem 0; font-weight: 600; text-align: right;">LM Studio (localhost)</td>
                </tr>
                <tr style="border-bottom: 1px solid var(--border-light);">
                    <td style="padding: 0.5rem 0; color: var(--text-muted);">Strategy</td>
                    <td style="padding: 0.5rem 0; font-weight: 600; text-align: right;">DB-first, AI-fallback</td>
                </tr>
                <tr style="border-bottom: 1px solid var(--border-light);">
                    <td style="padding: 0.5rem 0; color: var(--text-muted);">Offline Mode</td>
                    <td style="padding: 0.5rem 0; font-weight: 600; text-align: right;">Full functionality</td>
                </tr>
                <tr style="border-bottom: 1px solid var(--border-light);">
                    <td style="padding: 0.5rem 0; color: var(--text-muted);">Intent Classification</td>
                    <td style="padding: 0.5rem 0; font-weight: 600; text-align: right;">6 intents, keyword-based</td>
                </tr>
                <tr style="border-bottom: 1px solid var(--border-light);">
                    <td style="padding: 0.5rem 0; color: var(--text-muted);">Ingredient Matching</td>
                    <td style="padding: 0.5rem 0; font-weight: 600; text-align: right;">Fuzzy match to food DB</td>
                </tr>
                <tr>
                    <td style="padding: 0.5rem 0; color: var(--text-muted);">Substitution Engine</td>
                    <td style="padding: 0.5rem 0; font-weight: 600; text-align: right;">Category-based CO2 swap</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)


def _render_workflow() -> None:
    st.markdown("""
    <div class="profile-section">
        <h3>System Workflow</h3>
    </div>
    """, unsafe_allow_html=True)

    steps = [
        {
            "label": "User Input",
            "detail": "Ingredients (quick-select or text), cooking preferences, focus mode",
            "color": "#2196F3",
        },
        {
            "label": "Intent Classification",
            "detail": "parse_intent() identifies: greeting, recipe_request, modification, shopping_list, weekly_plan, question",
            "color": "#9C27B0",
        },
        {
            "label": "Recipe Search (DB)",
            "detail": "search_by_ingredients() in 2,000 recipe DB with CO2-weighted scoring. Returns immediately if found.",
            "color": "#27ae60",
        },
        {
            "label": "LLM Fallback",
            "detail": "If DB empty: Qwen3.5 generates recipe via structured prompt. Local LM Studio only.",
            "color": "#FF9800",
        },
        {
            "label": "CO2 Calculation",
            "detail": "Per-ingredient CO2 from aliments.json x quantity x country multiplier (52 countries)",
            "color": "#E53935",
        },
        {
            "label": "Enrichment",
            "detail": "CO2 label (Excellent -> Very High), comparison to national avg, substitution suggestions",
            "color": "#0097A7",
        },
        {
            "label": "Response",
            "detail": "Recipe card with CO2 badge, shopping list, weekly plan, or answer",
            "color": "#27ae60",
        },
    ]

    for i, step in enumerate(steps):
        is_last = i == len(steps) - 1
        arrow = "" if is_last else """
            <div style="display: flex; justify-content: center; padding: 0.25rem 0;">
                <div style="
                    width: 2px; height: 20px;
                    background: var(--border);
                "></div>
            </div>
            <div style="display: flex; justify-content: center; margin-bottom: 0.25rem;">
                <div style="
                    width: 0; height: 0;
                    border-left: 6px solid transparent;
                    border-right: 6px solid transparent;
                    border-top: 8px solid var(--border);
                "></div>
            </div>
        """

        st.markdown(f"""
        <div style="
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-left: 4px solid {step['color']};
            border-radius: var(--radius-sm);
            padding: 0.85rem 1.1rem;
            box-shadow: var(--shadow);
        ">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <div style="
                    background: {step['color']};
                    color: white;
                    min-width: 28px; height: 28px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 0.8rem;
                    font-weight: 700;
                    flex-shrink: 0;
                ">{i + 1}</div>
                <div>
                    <span style="font-weight: 700; color: var(--text); font-size: 0.95rem;">
                        {step['label']}
                    </span>
                    <br>
                    <span style="color: var(--text-muted); font-size: 0.82rem;">
                        {step['detail']}
                    </span>
                </div>
            </div>
        </div>
        {arrow}
        """, unsafe_allow_html=True)

    _render_data_sources()


def _render_data_sources() -> None:
    st.markdown("#### Data Sources")

    sources = [
        ("ADEME", "Agence de la Transition Ecologique - French food CO2 database (aliments.json)"),
        ("Our World in Data", "Country-level food system emissions (country_co2.json multipliers)"),
        ("Poore & Nemecek (2018)", "Science journal - comprehensive food lifecycle analysis across 119 countries"),
        ("FAO", "Food and Agriculture Organization - agricultural efficiency and supply chain data"),
        ("What's Cooking (Kaggle)", "39,774 recipes across 20 cuisines (processed to 2,000 best-match recipes)"),
    ]

    for name, desc in sources:
        st.markdown(f"""
        <div style="
            display: flex; align-items: baseline; gap: 0.5rem;
            padding: 0.4rem 0;
            border-bottom: 1px solid var(--border-light);
        ">
            <span style="font-weight: 700; color: var(--text); font-size: 0.88rem; white-space: nowrap;">
                {name}
            </span>
            <span style="color: var(--text-muted); font-size: 0.82rem;">- {desc}</span>
        </div>
        """, unsafe_allow_html=True)
