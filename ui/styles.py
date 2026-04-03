import streamlit as st


def load_css():
    st.markdown("""
    <style>
        /* ========== CSS VARIABLES ========== */
        :root {
            --primary: #27ae60;
            --primary-dark: #1e8449;
            --primary-light: #d5f5e3;
            --secondary: #2196F3;
            --secondary-light: #e3f2fd;
            --warning: #FF9800;
            --warning-light: #fff3e0;
            --danger: #E53935;
            --danger-light: #ffebee;
            --bg: #f8faf8;
            --bg-white: #ffffff;
            --bg-card: #ffffff;
            --bg-hover: #f0f7f0;
            --text: #1b4332;
            --text-secondary: #495057;
            --text-muted: #6c757d;
            --border: #dee2e6;
            --border-light: #e9ecef;
            --shadow: 0 2px 12px rgba(0,0,0,0.06);
            --shadow-hover: 0 4px 20px rgba(0,0,0,0.1);
            --radius: 12px;
            --radius-sm: 8px;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --primary: #2ecc71;
                --primary-dark: #27ae60;
                --primary-light: #1b4332;
                --secondary: #64b5f6;
                --secondary-light: #1a2940;
                --warning: #ffb74d;
                --warning-light: #3e2f1f;
                --danger: #ef5350;
                --danger-light: #3e1f1f;
                --bg: #0d1117;
                --bg-white: #161b22;
                --bg-card: #1c2333;
                --bg-hover: #1f2937;
                --text: #e6edf3;
                --text-secondary: #b1bac4;
                --text-muted: #768390;
                --border: #30363d;
                --border-light: #21262d;
                --shadow: 0 2px 12px rgba(0,0,0,0.3);
                --shadow-hover: 0 4px 20px rgba(0,0,0,0.4);
            }
        }

        /* ========== GLOBAL ========== */
        .stApp {
            background-color: var(--bg);
        }

        .main .block-container {
            padding-top: 1.5rem;
            padding-bottom: 1.5rem;
            max-width: 1200px;
        }

        /* ========== TABS - NAVIGATION FIX ========== */
        .stTabs {
            background-color: var(--bg-white);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            padding: 0.5rem;
            margin-bottom: 1.5rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.25rem;
            background-color: var(--bg);
            border-radius: var(--radius-sm);
            padding: 0.25rem;
            height: auto;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: var(--radius-sm);
            padding: 0.6rem 1.5rem;
            font-weight: 600;
            font-size: 0.95rem;
            color: var(--text-muted);
            background-color: transparent;
            border: none;
            transition: all 0.2s ease;
        }

        .stTabs [data-baseweb="tab"]:hover {
            background-color: var(--bg-hover);
            color: var(--primary);
        }

        .stTabs [aria-selected="true"] {
            background-color: var(--primary) !important;
            color: white !important;
            box-shadow: 0 2px 8px rgba(39,174,96,0.3);
        }

        .stTabs [data-baseweb="tab-highlight"] {
            display: none !important;
        }

        /* ========== BUTTONS ========== */
        .stButton > button[kind="primary"] {
            background-color: var(--primary);
            color: white;
            border: none;
            border-radius: var(--radius-sm);
            font-weight: 600;
            transition: all 0.2s ease;
        }

        .stButton > button[kind="primary"]:hover {
            background-color: var(--primary-dark);
            box-shadow: 0 4px 12px rgba(39,174,96,0.3);
        }

        .stButton > button[kind="secondary"] {
            background-color: var(--bg-white);
            color: var(--text);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            font-weight: 500;
            transition: all 0.2s ease;
        }

        .stButton > button[kind="secondary"]:hover {
            border-color: var(--primary);
            color: var(--primary);
        }

        /* ========== CARDS ========== */
        .eco-card {
            background-color: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: var(--radius);
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: var(--shadow);
            transition: box-shadow 0.2s ease;
        }

        .eco-card:hover {
            box-shadow: var(--shadow-hover);
        }

        .eco-card h3 {
            color: var(--primary);
            margin-top: 0;
            border-bottom: 2px solid var(--primary-light);
            padding-bottom: 0.5rem;
        }

        .feature-card {
            background-color: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: var(--radius);
            padding: 1.5rem;
            text-align: center;
            box-shadow: var(--shadow);
            transition: all 0.3s ease;
            border-top: 3px solid var(--primary);
        }

        .feature-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-hover);
        }

        .feature-card .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }

        .feature-card h4 {
            color: var(--primary);
            margin-bottom: 0.5rem;
        }

        .feature-card p {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        /* ========== HERO SECTION ========== */
        .hero-section {
            text-align: center;
            padding: 3rem 2rem;
            background: linear-gradient(135deg, var(--primary-light) 0%, var(--bg-white) 50%, var(--secondary-light) 100%);
            border-radius: var(--radius);
            margin-bottom: 2rem;
        }

        .hero-section h1 {
            color: var(--primary-dark);
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }

        .hero-section .hero-subtitle {
            color: var(--text-secondary);
            font-size: 1.2rem;
            margin-bottom: 1rem;
        }

        .hero-section .hero-tagline {
            color: var(--primary);
            font-size: 0.95rem;
            font-weight: 600;
        }

        /* ========== STAT CARDS ========== */
        .stat-card {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 1.25rem;
            border-radius: var(--radius);
            text-align: center;
            box-shadow: var(--shadow);
        }

        .stat-card h2 {
            margin: 0;
            font-size: 2rem;
        }

        .stat-card p {
            margin: 0.25rem 0 0 0;
            opacity: 0.9;
            font-size: 0.85rem;
        }

        /* ========== CHAT MESSAGES ========== */
        .message-user {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 0.75rem 1.25rem;
            border-radius: 18px 18px 4px 18px;
            margin: 0.5rem 0;
            margin-left: auto;
            max-width: 75%;
            text-align: left;
            box-shadow: var(--shadow);
            word-wrap: break-word;
        }

        .message-assistant {
            background-color: var(--bg-card);
            border: 1px solid var(--border-light);
            color: var(--text);
            padding: 0.75rem 1.25rem;
            border-radius: 18px 18px 18px 4px;
            margin: 0.5rem 0;
            max-width: 75%;
            box-shadow: var(--shadow);
            word-wrap: break-word;
        }

        /* ========== CO2 BADGES ========== */
        .co2-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.85rem;
        }

        .co2-excellent { background-color: #d4edda; color: #155724; }
        .co2-low { background-color: #d1ecf1; color: #0c5460; }
        .co2-medium { background-color: #fff3cd; color: #856404; }
        .co2-high { background-color: #ffe5d0; color: #a04a00; }
        .co2-very-high { background-color: #f8d7da; color: #721c24; }

        /* ========== INGREDIENTS / STEPS ========== */
        .ingredient-chip {
            display: inline-block;
            background-color: var(--primary-light);
            border: 1px solid var(--primary);
            border-radius: 16px;
            padding: 0.2rem 0.7rem;
            margin: 0.2rem;
            font-size: 0.85rem;
            color: var(--primary-dark);
        }

        .step-number {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            background-color: var(--primary);
            color: white;
            border-radius: 50%;
            font-weight: 600;
            font-size: 0.85rem;
            flex-shrink: 0;
        }

        .recipe-step {
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
            margin-bottom: 0.5rem;
            padding: 0.6rem;
            background-color: var(--bg-hover);
            border-radius: var(--radius-sm);
        }

        /* ========== SHOPPING ========== */
        .shopping-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--border-light);
        }

        .shopping-item:last-child {
            border-bottom: none;
        }

        .price-tag {
            color: var(--primary);
            font-weight: 600;
        }

        /* ========== SUBSTITUTIONS ========== */
        .substitution-card {
            background-color: var(--primary-light);
            border-left: 4px solid var(--primary);
            padding: 0.75rem 1rem;
            margin: 0.5rem 0;
            border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
        }

        /* ========== SIDEBAR ========== */
        .sidebar-logo {
            text-align: center;
            padding: 1rem 0;
        }

        .sidebar-logo h2 {
            color: var(--primary);
            margin-bottom: 0;
        }

        .sidebar-logo small {
            color: var(--text-muted);
        }

        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 0.5rem;
        }

        .status-dot-online { background-color: var(--primary); }
        .status-dot-offline { background-color: var(--danger); }

        /* ========== PROFILE FORM ========== */
        .profile-section {
            background-color: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: var(--radius);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: var(--shadow);
        }

        .profile-section h3 {
            color: var(--primary);
            border-bottom: 2px solid var(--primary-light);
            padding-bottom: 0.5rem;
            margin-top: 0;
        }

        /* ========== PROGRESS BAR ========== */
        .eco-progress {
            background-color: var(--border-light);
            border-radius: 10px;
            overflow: hidden;
            height: 12px;
            margin: 0.5rem 0;
        }

        .eco-progress-bar {
            height: 100%;
            border-radius: 10px;
            transition: width 0.5s ease;
        }

        /* ========== HOW IT WORKS STEPS ========== */
        .step-card {
            text-align: center;
            padding: 1.5rem;
        }

        .step-card .step-icon {
            width: 60px;
            height: 60px;
            background-color: var(--primary-light);
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            margin-bottom: 1rem;
            color: var(--primary-dark);
        }

        .step-card h4 {
            color: var(--text);
            margin-bottom: 0.5rem;
        }

        .step-card p {
            color: var(--text-muted);
            font-size: 0.9rem;
        }

        /* ========== FOOTER ========== */
        .footer {
            text-align: center;
            padding: 1rem;
            color: var(--text-muted);
            font-size: 0.85rem;
            border-top: 1px solid var(--border-light);
            margin-top: 2rem;
        }

        /* ========== NUMBER METRIC ========== */
        .metric-row {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .metric-box {
            flex: 1;
            min-width: 140px;
            background-color: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: var(--radius-sm);
            padding: 1rem;
            text-align: center;
        }

        .metric-box .metric-value {
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--primary);
        }

        .metric-box .metric-label {
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 0.25rem;
        }

        /* ========== CONVERSATION HISTORY ========== */
        .conversation-active {
            background-color: var(--primary-light);
            border: 1px solid var(--primary);
            border-radius: var(--radius-sm);
            padding: 0.5rem 0.75rem;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: var(--primary-dark);
            font-size: 0.9rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .conversation-item {
            padding: 0.4rem 0;
            border-bottom: 1px solid var(--border-light);
        }

        .conversation-item:last-child {
            border-bottom: none;
        }

        .conversation-item-title {
            font-weight: 600;
            font-size: 0.85rem;
            color: var(--text);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .conversation-item-meta {
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        /* ========== RESPONSIVE ========== */
        @media (max-width: 768px) {
            .hero-section {
                padding: 2rem 1rem;
            }

            .hero-section h1 {
                font-size: 1.8rem;
            }

            .eco-card {
                padding: 1rem;
            }

            .stat-card h2 {
                font-size: 1.5rem;
            }

            .message-user, .message-assistant {
                max-width: 90%;
            }
        }
    </style>
    """, unsafe_allow_html=True)


def render_co2_badge(co2_kg: float, label_info: dict) -> str:
    label = label_info.get('label', 'Unknown')
    emoji = label_info.get('emoji', '')

    if co2_kg <= 0.5:
        css_class = 'co2-excellent'
    elif co2_kg <= 1.5:
        css_class = 'co2-low'
    elif co2_kg <= 3.0:
        css_class = 'co2-medium'
    elif co2_kg <= 5.0:
        css_class = 'co2-high'
    else:
        css_class = 'co2-very-high'

    return f'<span class="co2-badge {css_class}">{emoji} {label} ({co2_kg:.2f} kg CO2)</span>'


def render_ingredient_chip(name: str, quantity_g: int = None) -> str:
    text = f"{name}"
    if quantity_g:
        text += f" ({quantity_g}g)"
    return f'<span class="ingredient-chip">{text}</span>'


def render_step(step_number: int, instruction: str) -> str:
    return f'''
    <div class="recipe-step">
        <span class="step-number">{step_number}</span>
        <span>{instruction}</span>
    </div>
    '''


def render_message(role: str, content: str) -> str:
    css_class = f"message-{role}"
    return f'<div class="{css_class}">{content}</div>'
