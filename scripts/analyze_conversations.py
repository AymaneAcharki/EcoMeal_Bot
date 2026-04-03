"""
Analyze all conversations in data/conversations/
Extract prompts, test them, and save analysis results
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from profile.manager import ProfileManager
from profile.models import UserProfile
from chat.engine import ChatEngine
import config


def load_conversation(filepath):
    """Load a conversation JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_user_prompts(conversation):
    """Extract all user messages from a conversation."""
    prompts = []
    for msg in conversation.get('messages', []):
        if msg.get('role') == 'user':
            prompts.append(msg.get('content', ''))
    return prompts


def get_pantry_for_profile(user_id):
    """Get pantry ingredients based on profile."""
    pantries = {
        "Marie_France": ["lentils", "tomatoes", "onions", "garlic", "olive oil", "spinach"],
        "John_USA": ["chicken", "black beans", "rice", "tomatoes", "peppers", "onions"],
        "Kenji_Japan": ["fish", "rice", "soy sauce", "ginger", "tofu", "seaweed"],
        "Priya_India": ["chickpeas", "tomatoes", "onions", "ginger", "garlic", "spices"],
        "Emma_UK": ["pasta", "tomatoes", "spinach", "garlic", "olive oil", "cheese"],
        "Ahmed_Morocco": ["lamb", "prunes", "almonds", "onions", "spices", "olive oil"],
        "Sven_Sweden": ["salmon", "potatoes", "dill", "cucumber", "lemon", "olive oil"],
        "Lucas_Brazil": ["black beans", "rice", "onions", "garlic", "peppers", "tomatoes"],
    }
    return pantries.get(user_id, [])


def run_conversation_test(engine, prompts, pantry):
    """Run prompts through the chat engine and collect responses."""
    results = []
    for prompt in prompts:
        response = engine.process_message(prompt, pantry_items=pantry, constraints={"focus_mode": "co2"})
        results.append({
            "prompt": prompt,
            "response_type": response.get("type", "unknown"),
            "response_message": response.get("message", "")[:200] + "...",
            "has_recipe": response.get("type") == "recipe",
            "recipe_name": response.get("recipe", {}).get("name", "") if response.get("type") == "recipe" else None,
            "co2_kg": response.get("recipe", {}).get("co2_info", {}).get("total_co2_kg", 0) if response.get("type") == "recipe" else 0
        })
    return results


def analyze_all_conversations():
    """Main analysis function."""
    profile_manager = ProfileManager()
    conversations_dir = config.CONVERSATIONS_DIR

    output_file = config.BASE_DIR / "analysis_results.txt"


    results = []
    results.append("=" * 80)
    results.append("ECOMEAL - CONVERSATION ANALYSIS REPORT")
    results.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    results.append("=" * 80)
    results.append("")

    # Get all conversation files
    conv_files = sorted(conversations_dir.glob("conv_*.json"))

    total_tests = 0
    successful_tests = 0
    recipes_generated = 0

    for conv_file in conv_files:
        conv = load_conversation(conv_file)
        conv_id = conv.get('id', conv_file.stem)
        user_id = conv.get('user_id', 'unknown')
        title = conv.get('title', 'Untitled')

        results.append("-" * 60)
        results.append(f"CONVERSATION: {conv_id}")
        results.append(f"Title: {title}")
        results.append(f"User: {user_id}")
        results.append("-" * 60)

        # Load profile
        try:
            profile = profile_manager.load_profile(user_id)
        except:
            profile = UserProfile(user_id=user_id)

        # Create engine
        engine = ChatEngine(profile)
        pantry = get_pantry_for_profile(user_id)

        # Extract prompts
        prompts = extract_user_prompts(conv)
        results.append(f"Prompts: {len(prompts)}")
        results.append(f"Pantry: {', '.join(pantry[:5])}...")
        results.append("")

        # Test each prompt
        for i, prompt in enumerate(prompts):
            total_tests += 1
            response = engine.process_message(prompt, pantry_items=pantry, constraints={"focus_mode": "co2"})

            resp_type = response.get("type", "unknown")
            is_recipe = resp_type == "recipe"

            if is_recipe:
                successful_tests += 1
                recipes_generated += 1
                recipe_name = response.get("recipe", {}).get("name", "Unknown")
                co2 = response.get("recipe", {}).get("co2_info", {}).get("total_co2_kg", 0)
                co2_label = response.get("recipe", {}).get("co2_label", {}).get("label", "?")
                results.append(f"  [{i+1}] USER: {prompt[:60]}...")
                results.append(f"      RECIPE: {recipe_name}")
                results.append(f"      CO2: {co2} kg ({co2_label})")
            else:
                msg = response.get("message", "")[:100]
                results.append(f"  [{i+1}] USER: {prompt[:60]}...")
                results.append(f"      RESPONSE ({resp_type}): {msg}...")
            results.append("")

        results.append("")

    # Summary
    results.append("=" * 80)
    results.append("SUMMARY")
    results.append("=" * 80)
    results.append(f"Total conversations tested: {len(conv_files)}")
    results.append(f"Total prompts executed: {total_tests}")
    results.append(f"Recipes generated: {recipes_generated}")
    results.append(f"Success rate: {recipes_generated}/{total_tests} ({100*recipes_generated/max(total_tests,1):.1f}%)")
    results.append("")
    results.append(f"Analysis saved to: {output_file}")

    # Write to file
    output_text = "\n".join(results)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output_text)

    return output_text


if __name__ == "__main__":
    print("Running conversation analysis...")
    print()
    output = analyze_all_conversations()
    print(output)
