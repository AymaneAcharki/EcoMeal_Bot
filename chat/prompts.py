from typing import Dict, List


SYSTEM_PROMPT = """You are EcoChef, a sustainable cooking assistant for UN SDG 12 (Responsible Consumption).

ROLE:
Help users cook delicious meals while reducing their carbon footprint. Generate recipes, calculate CO2 impact, and suggest sustainable substitutions.

STRICT RULES:
1. ONLY answer about: recipes, cooking, food CO2, sustainable substitutions, nutrition
2. Off-topic -> "I specialize in sustainable cooking. Ask me about recipes or food environmental impact."
3. Be concise and practical (max 300 words per response)
4. Every recipe MUST follow the RECIPE FORMAT below - no exceptions
5. When generating JSON, output ONLY valid JSON, no extra text before or after

CO2 DATA (kg CO2 per kg of food):
- Beef: 27.0 | Lamb: 20.0 | Pork: 7.6 | Chicken: 6.9 | Fish: 6-12
- Eggs: 4.8 | Cheese: 13.5 | Butter: 11.9 | Cream: 7.5
- Tofu: 2.0 | Tempeh: 1.5 | Lentils: 0.9 | Chickpeas: 0.8 | Beans: 1.0
- Vegetables: 0.3-1.5 | Fruits: 0.3-1.2
- Rice: 2.7 | Pasta: 1.5 | Potatoes: 0.2 | Bread: 1.0
- Quinoa: 2.4 | Couscous: 1.1 | Oats: 1.2
- Olive oil: 3.8 | Vegetable oil: 2.5 | Coconut milk: 2.1

CO2 LABELS per meal (French avg = 2.5 kg):
- Excellent: <= 0.5 kg | Low: 0.5-1.5 kg | Medium: 1.5-3.0 kg
- High: 3.0-5.0 kg | Very High: > 5.0 kg

TARGET: Keep recipes under 2.0 kg CO2 per serving.

SUBSTITUTIONS (suggest when relevant):
- Beef -> Lentils (97% less CO2) or Chickpeas (96% less)
- Lamb -> Chickpeas (96% less CO2)
- Pork -> Tofu (74% less CO2) or Mushrooms (95% less)
- Chicken -> Mushrooms (71% less CO2) or Tofu (71% less)
- Fish -> Lentils (85% less CO2)
- Butter -> Olive oil (68% less CO2) or plant-based spread
- Cream -> Coconut milk (72% less CO2) or oat cream
- Cheese -> Nutritional yeast or cashew cream (79% less CO2)

AUTO-SUGGESTIONS (always apply):
- If user picks red meat (beef/lamb) -> suggest plant-based alternative with CO2 savings
- If meal CO2 > 3 kg -> warn and propose substitutions
- Always mention environmental impact of the meal
- If user mentions allergies -> strictly exclude those ingredients
- Adjust complexity to user skill level (beginner/intermediate/advanced)
- Consider available appliances (oven, stovetop, microwave, air fryer, blender)
- Match cuisine preference if specified

RECIPE FORMAT (use this exact JSON structure):
{
  "name": "Recipe Name",
  "description": "Brief 1-2 sentence description",
  "ingredients": [
    {"name": "Ingredient Name", "quantity_g": 150}
  ],
  "steps": [
    "Step 1: Clear instruction with time/temp.",
    "Step 2: Clear instruction."
  ],
  "cooking_time_minutes": 30,
  "difficulty": "easy",
  "sustainability_tip": "1 sentence on reducing environmental impact."
}

INGREDIENT RULES:
- Always include quantity in grams for every ingredient
- Number ingredients realistically: main ingredients 100-300g, spices 2-10g, oils 10-30ml
- Use common ingredient names (not brand names)
- Maximum 12 ingredients per recipe
- Default serving size: 2 people (adjust quantities for household size)

STEP RULES:
- 4 to 8 steps per recipe
- Each step must be a clear, actionable instruction
- Start with prep (chop, dice, mince), then cook, then serve
- Include cooking times and temperatures in steps
- Be specific: "saute for 5 minutes over medium heat" not "cook"

When asked for a recipe in JSON: output ONLY the JSON object, no markdown, no backticks, no extra text."""


def build_recipe_prompt(ingredients: List[str], profile: Dict,
                        constraints: Dict = None,
                        focus_mode: str = "co2") -> str:
    """Build a recipe generation prompt with user context."""
    diet = profile.get('diet_type', 'omnivore')
    allergies = profile.get('allergies', [])
    max_time = profile.get('max_cooking_time', 60)
    skill = profile.get('skill_level', 'beginner')
    household = profile.get('household_size', 2)
    cuisines = profile.get('cuisine_preferences', [])

    prompt = f"Generate a recipe using these ingredients: {', '.join(ingredients)}.\n\n"
    prompt += f"USER PROFILE:\n"
    prompt += f"- Diet: {diet}\n"
    prompt += f"- Household size: {household} people\n"
    prompt += f"- Skill level: {skill}\n"
    prompt += f"- Max cooking time: {max_time} minutes\n"

    if allergies:
        prompt += f"- ALLERGIES (strictly avoid): {', '.join(allergies)}\n"

    if cuisines:
        prompt += f"- Cuisine preferences: {', '.join(cuisines)}\n"

    if constraints:
        if 'max_co2' in constraints:
            prompt += f"- Maximum CO2 per serving: {constraints['max_co2']} kg\n"
        if 'appliances' in constraints:
            prompt += f"- Available appliances: {', '.join(constraints['appliances'])}\n"
        if 'difficulty' in constraints:
            prompt += f"- Difficulty level: {constraints['difficulty']}\n"

    focus_hints = {
        "co2": "FOCUS: Minimize CO2 footprint. Prefer plant-based proteins, local ingredients.\n",
        "nutri": "FOCUS: Maximize nutritional value. Include protein, fiber, vitamins.\n",
        "eco": "FOCUS: Budget-friendly and sustainable. Use affordable, seasonal ingredients.\n"
    }
    if focus_mode in focus_hints:
        prompt += focus_hints[focus_mode]

    prompt += "\nRespond with ONLY a valid JSON recipe following the format in your system prompt."
    return prompt


def build_recipe_suggestion_prompt(ingredients: List[str],
                                   matched_recipes: List[Dict],
                                   profile: Dict) -> str:
    """Prompt for LLM to present database recipes nicely."""
    prompt = f"The user has these ingredients: {', '.join(ingredients)}.\n\n"
    prompt += "I found these matching recipes from the database:\n\n"

    for i, r in enumerate(matched_recipes[:3], 1):
        name = r.get('name', 'Unknown')
        cuisine = r.get('cuisine', 'unknown')
        co2 = r.get('co2_total_kg', 2.5)
        ing_count = r.get('ingredient_count', 0)
        prompt += f"{i}. {name} ({cuisine}, {co2:.2f} kg CO2, {ing_count} ingredients)\n"

    prompt += "\nSelect the best match and present it as a complete recipe in JSON format."
    prompt += " Adjust ingredient quantities for the user's household size."
    prompt += " Output ONLY the JSON, no extra text."
    return prompt


def build_shopping_list_prompt(recipe_ingredients: List[Dict],
                               pantry_items: List[str],
                               focus_items: List[str] = None) -> str:
    """Prompt for generating a focused shopping list."""
    recipe_items = [i.get('name', 'Unknown') for i in recipe_ingredients]

    prompt = "Generate a shopping list comparing recipe needs with pantry.\n\n"
    prompt += f"Recipe needs: {', '.join(recipe_items)}\n"
    prompt += f"Already in pantry: {', '.join(pantry_items) if pantry_items else 'Nothing listed'}\n"

    if focus_items:
        prompt += f"\nFOCUS ON: {', '.join(focus_items)} (prioritize these categories)\n"

    prompt += "\nRespond in JSON format ONLY:\n"
    prompt += "{\n"
    prompt += '  "missing_items": [{"name": "item", "quantity": "100g", "category": "vegetables"}],\n'
    prompt += '  "estimated_cost_eur": 0.0,\n'
    prompt += '  "eco_tips": ["Buy seasonal", "Choose local"]\n'
    prompt += "}"
    return prompt


def build_follow_up_prompt(previous_recipe: Dict, modification: str,
                          focus_mode: str = "co2") -> str:
    """Prompt for modifying an existing recipe."""
    prompt = f"The user wants to modify the previous recipe.\n\n"
    prompt += f"Previous recipe: {previous_recipe.get('name', 'Unknown')}\n"
    prompt += f"Modification request: {modification}\n\n"

    if focus_mode == "co2":
        prompt += "When modifying, try to reduce CO2 footprint if possible.\n"
    elif focus_mode == "nutri":
        prompt += "When modifying, try to improve nutritional value.\n"
    elif focus_mode == "eco":
        prompt += "When modifying, try to keep it budget-friendly.\n"

    prompt += "Generate an updated recipe in JSON format following the same structure."
    prompt += " Output ONLY the JSON, no extra text."
    return prompt


def build_intent_classify_prompt(user_message: str) -> str:
    prompt = f"""Classify the user's intent from this message: "{user_message}"

Possible intents:
- recipe_request: User wants a new recipe
- modification: User wants to modify the previous recipe
- shopping_list: User wants a shopping list
- question: User has a question about cooking/sustainability/nutrition
- greeting: User is greeting the bot
- weekly_plan: User wants a weekly meal plan

Respond with only the intent label, nothing else.
Example: recipe_request"""

    return prompt


def build_weekly_plan_prompt(profile: Dict, pantry_items: List[str],
                            focus_mode: str = "co2") -> str:
    """Prompt for generating a weekly meal plan."""
    diet = profile.get('diet_type', 'omnivore')
    max_time = profile.get('max_cooking_time', 60)
    budget = profile.get('weekly_budget', 100)
    household = profile.get('household_size', 2)
    cuisines = profile.get('cuisine_preferences', [])

    prompt = "Generate a 7-day meal plan.\n\n"
    prompt += f"USER PROFILE:\n"
    prompt += f"- Diet: {diet}\n"
    prompt += f"- Max cooking time per meal: {max_time} minutes\n"
    prompt += f"- Weekly budget: {budget} EUR\n"
    prompt += f"- Household size: {household} people\n"

    if cuisines:
        prompt += f"- Cuisine preferences: {', '.join(cuisines)}\n"

    if pantry_items:
        prompt += f"- Available ingredients: {', '.join(pantry_items)}\n"

    focus_hints = {
        "co2": "FOCUS: Minimize weekly CO2 footprint.\n",
        "nutri": "FOCUS: Balanced nutrition throughout the week.\n",
        "eco": "FOCUS: Stay within budget, use affordable ingredients.\n"
    }
    if focus_mode in focus_hints:
        prompt += focus_hints[focus_mode]

    prompt += "\nRespond in JSON format ONLY:\n"
    prompt += "{\n"
    prompt += '  "days": [\n'
    prompt += '    {"day": "Monday", "meal": "Recipe name", "co2_kg": 1.5, "ingredients": ["list"]},\n'
    prompt += '    {"day": "Tuesday", ...},\n'
    prompt += '  ],\n'
    prompt += '  "total_estimated_cost_eur": 0.0,\n'
    prompt += '  "total_estimated_co2_kg": 0.0\n'
    prompt += "}"
    return prompt
