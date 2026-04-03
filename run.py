import sys
import subprocess
import importlib
import json
import time
import os
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

BASE_DIR = Path(__file__).parent
REQUIREMENTS_FILE = BASE_DIR / "requirements.txt"
APP_FILE = BASE_DIR / "app.py"
LM_STUDIO_URL = "http://localhost:1234/v1/models"

MIN_PYTHON = (3, 10)
REQUIRED_PACKAGES = {
    "streamlit": "1.29.0",
    "openai": "1.0.0",
    "requests": "2.28.0"
}

REQUIRED_FILES = [
    "config.py",
    "app.py",
    "requirements.txt",
    "data/aliments.json",
    "data/prices.json",
    "data/seasons.json",
    "data/recipes/recipes_db.json",
    "chat/__init__.py",
    "chat/engine.py",
    "chat/prompts.py",
    "chat/parser.py",
    "chat/history.py",
    "core/__init__.py",
    "core/co2.py",
    "core/ingredients.py",
    "core/shopping.py",
    "core/budget.py",
    "core/substitutions.py",
    "profile/__init__.py",
    "profile/models.py",
    "profile/manager.py",
    "profile/defaults.py",
    "ui/__init__.py",
    "ui/styles.py",
    "ui/sidebar.py",
    "ui/chat_area.py",
    "ui/recipe_card.py",
    "ui/shopping_list.py",
    "ui/weekly_tab.py",
    "ui/welcome_tab.py",
    "ui/profile_tab.py",
]

BANNER = r"""
 ____
|  _ \  ___  ___ _ __   ___  _ __  ___  ___
| | | |/ _ \/ _ \ '_ \ / _ \| '_ \/ __|/ _ \
| |_| |  __/  __/ |_) | (_) | | | \__ \  __/
|____/ \___|\___| .__/ \___/|_| |_|___/\___|
                |_|
        Sustainable Cooking Assistant
        UN SDG 12 - Responsible Consumption
"""

COLORS = {
    "green": "\033[92m",
    "red": "\033[91m",
    "yellow": "\033[93m",
    "cyan": "\033[96m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "reset": "\033[0m"
}


def cprint(text, color="reset"):
    print(f"{COLORS.get(color, '')}{text}{COLORS['reset']}")


def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    cprint(BANNER, "cyan")
    cprint("=" * 52, "dim")
    print()


def check_python_version():
    cprint("[1/6] Checking Python version...", "bold")
    version = sys.version_info
    
    if version >= MIN_PYTHON:
        cprint(f"      Python {version.major}.{version.minor}.{version.micro} OK", "green")
        return True
    
    cprint(f"      Python {version.major}.{version.minor}.{version.micro} FAIL", "red")
    cprint(f"      Required: Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+", "yellow")
    return False


def check_required_files():
    cprint("[2/6] Checking project files...", "bold")
    missing = []
    
    for filepath in REQUIRED_FILES:
        full_path = BASE_DIR / filepath
        if not full_path.exists():
            missing.append(filepath)
            cprint(f"      MISSING: {filepath}", "red")
    
    if not missing:
        cprint(f"      {len(REQUIRED_FILES)} files OK", "green")
        return True
    
    cprint(f"      {len(missing)} file(s) missing", "red")
    return False


def check_requirements():
    cprint("[3/6] Checking dependencies...", "bold")
    all_ok = True
    installed = []
    to_install = []
    
    for package, min_version in REQUIRED_PACKAGES.items():
        try:
            mod = importlib.import_module(package)
            ver = getattr(mod, "__version__", "0.0.0")
            
            ver_parts = [int(x) for x in ver.split(".")[:3]]
            min_parts = [int(x) for x in min_version.split(".")[:3]]
            
            if ver_parts >= min_parts:
                installed.append(f"{package}=={ver}")
            else:
                to_install.append(package)
                cprint(f"      {package}: {ver} (need {min_version}+) - will upgrade", "yellow")
                all_ok = False
        except ImportError:
            to_install.append(package)
            cprint(f"      {package}: NOT INSTALLED - will install", "yellow")
            all_ok = False
    
    if installed:
        for item in installed:
            cprint(f"      {item} OK", "green")
    
    if to_install:
        cprint(f"      Installing {len(to_install)} package(s)...", "yellow")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--quiet"] + to_install,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            cprint(f"      Installed successfully", "green")
            return True
        except subprocess.CalledProcessError:
            cprint(f"      Installation failed", "red")
            return False
    
    return all_ok


def check_modules():
    cprint("[4/6] Checking module imports...", "bold")
    modules_to_test = [
        ("config", "BASE_DIR, LM_STUDIO_MODEL, CO2_THRESHOLDS"),
        ("core", "load_aliments_db, calculate_meal_co2, get_co2_label, IngredientMatcher, BudgetManager"),
        ("profile", "UserProfile, ProfileManager, CHOICES"),
        ("chat", "ChatEngine, extract_json, parse_recipe, parse_intent, ConversationHistory"),
        ("ui", "render_sidebar, render_chat_area, render_recipe_card, render_shopping_list, render_weekly_tab, render_welcome_tab, render_profile_tab, load_css"),
    ]
    
    failed = []
    
    for module_name, attrs in modules_to_test:
        try:
            mod = importlib.import_module(module_name)
            for attr in attrs.split(", "):
                if not hasattr(mod, attr.strip()):
                    raise AttributeError(f"{module_name}.{attr.strip()}")
            cprint(f"      {module_name} OK", "green")
        except Exception as e:
            cprint(f"      {module_name} FAIL: {e}", "red")
            failed.append(module_name)
    
    if failed:
        return False
    
    data_ok = True
    data_files = {
        "aliments.json": BASE_DIR / "data" / "aliments.json",
        "prices.json": BASE_DIR / "data" / "prices.json",
        "seasons.json": BASE_DIR / "data" / "seasons.json",
        "recipes_db.json": BASE_DIR / "data" / "recipes" / "recipes_db.json",
    }
    
    for name, path in data_files.items():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                count = len(data.get("foods", data.get("prices", data.get("seasonal", data.get("recipes", [])))))
                cprint(f"      data/{name} OK ({count} entries)", "green")
        except Exception as e:
            cprint(f"      data/{name} FAIL: {e}", "red")
            data_ok = False
    
    return data_ok


def check_lm_studio():
    cprint("[5/6] Checking LM Studio connection...", "bold")
    
    try:
        response = urlopen(LM_STUDIO_URL, timeout=3)
        data = json.loads(response.read().decode())
        
        models = data.get("data", [])
        if models:
            model_id = models[0].get("id", "unknown")
            cprint(f"      LM Studio ONLINE", "green")
            cprint(f"      Model: {model_id}", "green")
            return True
        else:
            cprint(f"      LM Studio ONLINE but no model loaded", "yellow")
            cprint(f"      Load a model in LM Studio before chatting", "yellow")
            return True
    except (URLError, OSError):
        cprint(f"      LM Studio OFFLINE", "yellow")
        cprint(f"      App will start in offline mode (fallback recipes)", "yellow")
        cprint(f"      Start LM Studio and load Qwen3.5:0.8b for full features", "yellow")
        return True


def check_port():
    cprint("[6/6] Checking port availability...", "bold")
    
    import socket
    
    port = 8501
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(("localhost", port))
    sock.close()
    
    if result == 0:
        cprint(f"      Port {port} already in use (Streamlit may be running)", "yellow")
        cprint(f"      Opening existing instance in browser...", "yellow")
        return False
    
    cprint(f"      Port {port} available", "green")
    return True


def launch_streamlit():
    print()
    cprint("=" * 52, "dim")
    cprint("  LAUNCHING ECOMEAL BOT", "bold")
    cprint("=" * 52, "dim")
    print()
    cprint("  Local URL:  http://localhost:8501", "cyan")
    cprint("  Network:    http://localhost:8501", "dim")

    print()
    cprint("  LM Studio:  http://localhost:1234", "dim")
    cprint("  Docs:       https://opencode.ai", "dim")
    print()
    cprint("  Press Ctrl+C to stop", "yellow")
    cprint("=" * 52, "dim")
    print()
    
    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(APP_FILE), "--server.port=8501"],
            cwd=str(BASE_DIR)
        )
    except KeyboardInterrupt:
        cprint("\n  EcoMeal Bot stopped. Goodbye!", "cyan")


def main():
    print_banner()
    
    checks = [
        ("Python version", check_python_version),
        ("Project files", check_required_files),
        ("Dependencies", check_requirements),
        ("Module imports", check_modules),
        ("LM Studio", check_lm_studio),
        ("Port check", check_port),
    ]
    
    critical_failures = []
    warnings = []
    
    for name, check_fn in checks:
        try:
            result = check_fn()
            if result is False and name in ["Python version", "Project files", "Dependencies", "Module imports"]:
                critical_failures.append(name)
        except Exception as e:
            cprint(f"      {name} check error: {e}", "red")
            if name in ["Python version", "Project files", "Dependencies", "Module imports"]:
                critical_failures.append(name)
        print()
    
    if critical_failures:
        cprint("=" * 52, "red")
        cprint("  PRE-FLIGHT CHECK FAILED", "bold")
        cprint("=" * 52, "red")
        print()
        for failure in critical_failures:
            cprint(f"  X {failure}", "red")
        print()
        cprint("  Fix the issues above and try again.", "yellow")
        sys.exit(1)
    
    launch_streamlit()


if __name__ == "__main__":
    main()
