"""
IngredientMatcher - maps recipe ingredient names to aliments.json food items.

Uses a curated alias map per food for reliable matching, with category-aware
fallback scoring. Returns empty dict when no confident match exists, instead of
forcing a wrong match.
"""

import re
from typing import List, Dict, Optional, Tuple
from core.co2 import load_aliments_db


# Comprehensive alias map: canonical food name -> list of known ingredient names
# Each food in aliments.json has aliases covering common recipe language
FOOD_ALIASES: Dict[str, List[str]] = {
    # --- Meat ---
    "Beef (steak)": ["beef", "steak", "beef steak", "ribeye", "sirloin", "filet",
                      "beef fillet", "tenderloin", "new york strip", "t-bone",
                      "porterhouse", "flank steak", "round steak", "brisket",
                      "roast beef", "beef roast"],
    "Lamb": ["lamb", "leg of lamb", "lamb chops", "lamb shoulder", "lamb loin",
             "lamb rack", "ground lamb", "lamb stew", "lamb leg", "lamb shank",
             "mutton"],
    "Beef (minced)": ["minced beef", "ground beef", "beef mince", "hamburger meat",
                       "ground meat", "minced meat"],
    "Pork": ["pork", "pork chops", "pork loin", "pork shoulder", "pork belly",
             "pork tenderloin", "pork ribs", "pork roast", "pork stew",
             "pork fillet", "pork cubes", "pork cutlets", "bacon", "pancetta",
             "prosciutto", "ham", "chorizo", "sausage", "pork sausage",
             "salami", "speck", "guanciale", "lardons"],
    "Chicken": ["chicken", "chicken breast", "chicken thigh", "chicken leg",
                "chicken wing", "chicken drumstick", "chicken quarters",
                "whole chicken", "rotisserie chicken", "chicken tenderloin",
                "chicken pieces", "chicken fillet", "ground chicken"],
    "Turkey": ["turkey", "turkey breast", "turkey thigh", "ground turkey",
               "turkey slices", "turkey mince", "turkey leg"],
    # --- Fish ---
    "Fish (farmed salmon)": ["salmon", "salmon fillet", "smoked salmon",
                              "salmon steak", "fresh salmon", "atlantic salmon"],
    "Fish (cod)": ["cod", "cod fillet", "haddock", "pollock", "white fish",
                   "cod loin", "fresh cod"],
    "Fish (tuna canned)": ["tuna", "canned tuna", "tuna fish", "tuna steak",
                            "fresh tuna", "tuna in water", "tuna in oil"],
    "Shrimp": ["shrimp", "prawns", "jumbo shrimp", "tiger shrimp", "king prawn",
               "shelled shrimp", "deveined shrimp", "cooked shrimp"],
    # --- Dairy ---
    "Cheese (hard)": ["parmesan", "gruyere", "cheddar", "pecorino", "manchego",
                       "gouda", "comte", "emmental", "hard cheese", "aged cheese",
                       "asiago", "fontina", "edam", "grated cheese", "shredded cheese"],
    "Cheese (soft)": ["mozzarella", "feta", "ricotta", "cream cheese", "brie",
                       "camembert", "goat cheese", "cottage cheese", "mascarpone",
                       "soft cheese", "blue cheese", "roquefort", "gorgonzola",
                       "boursin", "fresh cheese", "cheese crumbles"],
    "Milk (cow)": ["milk", "whole milk", "skim milk", "semi-skimmed milk",
                    "2% milk", "whole milk", "hot milk"],
    "Yogurt": ["yogurt", "yoghurt", "greek yogurt", "plain yogurt", "natural yogurt"],
    "Butter": ["butter", "unsalted butter", "salted butter", "melted butter"],
    "Heavy cream": ["heavy cream", "whipping cream", "double cream", "fresh cream",
                     "heavy whipping cream", "single cream", "cooking cream"],
    "Sour cream": ["sour cream", "creme fraiche", "creme fraiche", "creme fraiche"],
    "Coconut milk": ["coconut milk", "coconut cream", "light coconut milk"],
    # --- Eggs ---
    "Eggs": ["egg", "eggs", "large eggs", "egg yolk", "egg white", "egg yolks",
             "egg whites", "whole eggs"],
    # --- Plant protein ---
    "Tofu": ["tofu", "firm tofu", "silken tofu", "soft tofu", "extra firm tofu"],
    "Tempeh": ["tempeh"],
    "Lentils": ["lentils", "red lentils", "green lentils", "brown lentils",
                "beluga lentils", "puy lentils", "lentil"],
    "Chickpeas": ["chickpeas", "garbanzo beans", "chickpea", "canned chickpeas"],
    "Beans (black)": ["black beans", "kidney beans", "white beans", "cannellini beans",
                       "navy beans", "pinto beans", "butter beans", "lima beans",
                       "great northern beans", "red beans", "beans", "canned beans",
                       "haricot beans", "baked beans"],
    "Seitan": ["seitan", "wheat gluten", "wheat meat"],
    # --- Carbs ---
    "Rice (white)": ["white rice", "basmati rice", "jasmine rice", "long grain rice",
                      "short grain rice", "rice", "plain rice", "cooked rice"],
    "Rice (brown)": ["brown rice", "wild rice", "whole grain rice"],
    "Pasta": ["pasta", "spaghetti", "penne", "fusilli", "linguine", "fettuccine",
              "tagliatelle", "rigatoni", "macaroni", "orecchiette", "farfalle",
              "bucatini", "pappardelle", "lasagna", "lasagne sheets", "noodles",
              "angel hair", "vermicelli", "cavatappi", "ziti", "orzo", "gnocchi"],
    "Bread (wheat)": ["bread", "white bread", "wheat bread", "baguette", "ciabatta",
                       "french bread", "sourdough bread", "country bread",
                       "bread crumbs", "bread cubes", "croutons", "panko",
                       "pita bread", "naan", "tortilla", "wrap"],
    "Quinoa": ["quinoa", "red quinoa", "white quinoa"],
    "Oats": ["oats", "rolled oats", "oatmeal", "steel cut oats", "quick oats"],
    "Cornstarch": ["cornstarch", "corn flour", "corn starch", "maizena"],
    "All-purpose flour": ["flour", "all-purpose flour", "plain flour", "wheat flour",
                          "maida", "ap flour", "self-rising flour", "white flour"],
    "Sugar": ["sugar", "white sugar", "granulated sugar", "caster sugar", "cane sugar"],
    "Brown sugar": ["brown sugar", "demerara", "raw sugar", "turbinado", "muscovado"],
    "Baking powder": ["baking powder", "baking soda"],
    "Corn tortillas": ["corn tortillas", "tortillas", "taco shells", "tostadas"],
    # --- Vegetables ---
    "Potatoes": ["potato", "potatoes", "russet potatoes", "red potatoes",
                  "yukon gold", "sweet potatoes", "yam", "new potatoes",
                  "fingerling potatoes", "boiling potatoes", "baking potatoes",
                  "mashed potatoes"],
    "Tomatoes": ["tomato", "tomatoes", "roma tomatoes", "cherry tomatoes",
                  "grape tomatoes", "beefsteak tomatoes", "vine tomatoes",
                  "plum tomatoes", "heirloom tomatoes", "fresh tomatoes",
                  "sun-dried tomatoes", "sun dried tomatoes"],
    "Carrots": ["carrot", "carrots", "baby carrots", "diced carrots",
                "sliced carrots", "matchstick carrots"],
    "Broccoli": ["broccoli", "broccoli florets", "broccoli rabe"],
    "Spinach": ["spinach", "baby spinach", "fresh spinach", "frozen spinach"],
    "Onions": ["onion", "onions", "yellow onion", "white onion", "red onion",
               "sweet onion", "vidalia onion", "spanish onion", "diced onion",
               "chopped onion", "sliced onion", "yellow onions", "finely chopped onion"],
    "Peppers": ["bell pepper", "bell peppers", "green pepper", "peppers"],
    "Zucchini": ["zucchini", "courgette", "courgettes", "yellow squash",
                  "summer squash"],
    "Mushrooms": ["mushroom", "mushrooms", "button mushrooms", "cremini mushrooms",
                   "portobello", "porcini", "shiitake", "oyster mushrooms",
                   "dried mushrooms", "wild mushrooms", "fresh mushrooms",
                   "dried porcini mushrooms", "mushroom"],
    "Garlic": ["garlic", "garlic cloves", "garlic clove", "minced garlic",
               "garlic press", "roasted garlic", "fresh garlic", "crushed garlic"],
    "Celery": ["celery", "celery stalk", "celery stalks", "celery ribs"],
    "Cabbage": ["cabbage", "green cabbage", "red cabbage", "savoy cabbage",
                "napa cabbage"],
    "Green beans": ["green beans", "string beans", "french beans", "haricots verts",
                     "snap beans", "runner beans"],
    "Green onions": ["green onion", "green onions", "scallion", "scallions",
                      "spring onion", "spring onions"],
    "Red bell pepper": ["red bell pepper", "red pepper", "roasted red pepper"],
    "Diced tomatoes": ["diced tomatoes", "crushed tomatoes", "canned tomatoes",
                        "tomatoes canned", "whole peeled tomatoes", "stewed tomatoes",
                        "passata", "tomato sauce"],
    "Shallots": ["shallot", "shallots", "eschalot"],
    # --- Fruits ---
    "Apples": ["apple", "apples", "green apple", "granny smith", "fuji apple",
               "golden delicious", "honeycrisp", "pink lady"],
    "Bananas": ["banana", "bananas", "plantain", "plantains"],
    "Oranges": ["orange", "oranges", "navel orange", "blood orange", "mandarin",
                "clementine", "tangerine"],
    "Berries": ["berries", "strawberries", "blueberries", "raspberries",
                "blackberries", "cranberries", "mixed berries", "fresh berries"],
    "Avocado": ["avocado", "avocados", "haas avocado", "ripe avocado"],
    "Lemon": ["lemon", "lemons", "lemon juice", "fresh lemon juice",
              "lemon zest", "lemon peel", "grated lemon peel", "lemon wedges"],
    "Lime": ["lime", "limes", "lime juice", "lime zest", "lime wedges",
             "key lime"],
    # --- Oils & fats ---
    "Olive oil": ["olive oil", "extra virgin olive oil", "extra-virgin olive oil",
                   "evoo", "virgin olive oil"],
    "Vegetable oil": ["vegetable oil", "canola oil", "sunflower oil", "rapeseed oil",
                       "cooking oil", "neutral oil", "corn oil", "safflower oil",
                       "peanut oil", "grapeseed oil"],
    "Sesame oil": ["sesame oil", "toasted sesame oil", "dark sesame oil"],
    # --- Condiments ---
    "Soy sauce": ["soy sauce", "soya sauce", "light soy sauce", "dark soy sauce",
                   "tamari", "shoyu"],
    "Honey": ["honey", "raw honey", "manuka honey"],
    "Vanilla extract": ["vanilla extract", "vanilla", "vanilla essence",
                         "vanilla bean", "vanilla paste"],
    "Chicken broth": ["chicken broth", "chicken stock", "chicken bouillon",
                       "bouillon cube", "stock cube", "bone broth",
                       "vegetable broth", "vegetable stock", "beef broth",
                       "beef stock"],
    "Tomato paste": ["tomato paste", "tomato puree", "tomato concentrate",
                      "double concentrate", "tube tomato paste"],
    "Salsa": ["salsa", "salsa verde", "pico de gallo", "enchilada sauce",
              "taco sauce"],
    "Rice vinegar": ["rice vinegar", "rice wine vinegar", "seasoned rice vinegar",
                      "mirin", "black vinegar"],
    "Fish sauce": ["fish sauce", "nam pla", "nuoc mam"],
    # --- Herbs & spices ---
    "Ginger": ["ginger", "fresh ginger", "ginger root", "ground ginger",
               "grated ginger", "minced ginger", "galangal"],
    "Cilantro": ["cilantro", "fresh cilantro", "coriander leaves", "coriander",
                  "fresh coriander", "chinese parsley"],
    "Parsley": ["parsley", "fresh parsley", "flat leaf parsley", "italian parsley",
                "curly parsley", "parsley leaves", "chopped fresh parsley",
                "italian parsley leaves", "flat-leaf parsley"],
    "Basil": ["basil", "fresh basil", "basil leaves", "sweet basil",
              "thai basil", "dried basil"],
    "Bay leaves": ["bay leaves", "bay leaf", "laurel", "dried bay leaves"],
    "Cumin": ["cumin", "ground cumin", "cumin seeds", "cumin seed", "jeera"],
    "Chili powder": ["chili powder", "chilli powder", "chile powder", "cayenne",
                      "cayenne pepper", "red pepper flakes", "chili flakes",
                      "crushed red pepper", "chipotle powder", "ancho powder",
                      "paprika", "smoked paprika", "hot paprika", "gochugaru"],
    "Lemon juice": ["lemon juice", "fresh lemon juice", "juice of lemon",
                     "juice of 1 lemon"],
}


# Category keywords: helps disambiguate when multiple matches are possible
CATEGORY_KEYWORDS = {
    "meat": ["beef", "lamb", "pork", "chicken", "turkey", "duck", "goose",
             "veal", "venison", "rabbit", "bacon", "ham", "sausage", "steak",
             "meat", "minced", "ground beef", "ground lamb", "ground pork",
             "ground chicken", "ground turkey", "prosciutto", "pancetta",
             "chorizo", "salami", "cutlet", "fillet", "tenderloin", "rib",
             "roast", "brisket", "shank", "loin", "leg of", "belly"],
    "fish": ["fish", "salmon", "tuna", "cod", "shrimp", "prawn", "sardine",
             "mackerel", "trout", "anchovy", "anchovies", "mussels", "clam",
             "clams", "oyster", "oysters", "scallop", "scallops", "crab",
             "lobster", "squid", "octopus", "sea bass", "sole", "tilapia",
             "haddock", "pollock", "hake", "halibut", "swordfish", "eel",
             "seafood", "shellfish"],
    "dairy": ["cheese", "milk", "cream", "butter", "yogurt", "yoghurt",
              "mozzarella", "parmesan", "feta", "ricotta", "brie", "gruyere"],
    "eggs": ["egg", "eggs", "yolk", "white"],
    "plant_protein": ["tofu", "tempeh", "lentils", "chickpeas", "beans",
                      "seitan", "legumes", "peas"],
    "carbs": ["rice", "pasta", "bread", "flour", "noodle", "quinoa", "oat",
              "tortilla", "couscous", "barley", "bulgur", "semolina"],
    "vegetables": ["potato", "tomato", "carrot", "onion", "garlic", "broccoli",
                   "spinach", "mushroom", "celery", "pepper", "zucchini",
                   "cabbage", "lettuce", "kale", "pea", "corn", "eggplant",
                   "cucumber", "turnip", "beet", "pumpkin", "squash", "radish",
                   "artichoke", "asparagus", "fennel", "leek"],
    "fruits": ["apple", "banana", "orange", "lemon", "lime", "berry",
               "strawberry", "blueberry", "mango", "pineapple", "peach",
               "pear", "grape", "cherry", "fig", "date", "coconut", "avocado"],
    "oils_fats": ["oil", "olive oil", "butter", "margarine", "lard", "ghee",
                  "shortening", "coconut oil"],
    "condiments": ["sauce", "paste", "vinegar", "broth", "stock", "salsa",
                   "soy", "honey", "ketchup", "mustard", "mayo", "mayonnaise",
                   " Worcestershire", "tapenade", "pesto", "chutney", "relish"],
    "herbs_spices": ["basil", "parsley", "cilantro", "mint", "thyme", "rosemary",
                     "oregano", "dill", "sage", "bay", "cumin", "cinnamon",
                     "turmeric", "paprika", "nutmeg", "ginger", "saffron",
                     "clove", "coriander", "cardamom", "star anise",
                     "chili", "cayenne", "pepper", "salt"],
}


class IngredientMatcher:
    def __init__(self, db: Dict = None):
        self.db = db or load_aliments_db()
        self._build_index()

    def _build_index(self):
        """Build lookup structures from aliments DB + alias map."""
        # name -> food dict (exact match on canonical names)
        self.food_by_name: Dict[str, Dict] = {}
        for food in self.db.get('foods', []):
            self.food_by_name[food.get('name', '').lower()] = food

        # alias -> (food, food_name) for all known aliases
        self.alias_to_food: Dict[str, Tuple[Dict, str]] = {}
        for food_name, aliases in FOOD_ALIASES.items():
            food = self.food_by_name.get(food_name.lower())
            if food:
                for alias in aliases:
                    self.alias_to_food[alias.lower()] = (food, food_name)

        # category -> list of foods
        self.category_foods: Dict[str, List[Dict]] = {}
        for food in self.db.get('foods', []):
            cat = food.get('category', '')
            if cat not in self.category_foods:
                self.category_foods[cat] = []
            self.category_foods[cat].append(food)

        # Build reverse lookup: detect category from ingredient name
        self.name_category_hints: Dict[str, str] = {}
        for cat, keywords in CATEGORY_KEYWORDS.items():
            for kw in keywords:
                self.name_category_hints[kw] = cat

    def match_ingredient(self, ingredient_name: str) -> Dict:
        """Match an ingredient name to the best food item in aliments.json.

        Priority:
        1. Exact alias match
        2. Alias contains ingredient name
        3. Ingredient name contains alias (with category awareness)
        4. Return {} (no match) instead of wrong match
        """
        name = ingredient_name.lower().strip()
        if not name:
            return {}

        # Remove common prefixes/suffixes that add noise
        clean = name
        for prefix in ["fresh ", "dried ", "diced ", "chopped ", "finely ",
                        "coarsely ", "minced ", "grated ", "sliced ", "crushed ",
                        "ground ", "whole ", "large ", "small ", "medium ",
                        "raw ", "cooked ", "canned ", "frozen ", "roasted "]:
            clean = clean.replace(prefix, "")
        clean = clean.strip()

        # Step 1: Exact alias match (highest confidence)
        if name in self.alias_to_food:
            return self.alias_to_food[name][0]
        if clean in self.alias_to_food:
            return self.alias_to_food[clean][0]

        # Step 2: Try each word from longest to shortest
        words_all = name.split()
        words_clean = clean.split() if clean != name else words_all

        # Try compound words first (2-word combos), then single words
        for word_list in [words_clean, words_all]:
            # Try 2-word combinations
            for i in range(len(word_list) - 1):
                bigram = f"{word_list[i]} {word_list[i+1]}"
                if bigram in self.alias_to_food:
                    return self.alias_to_food[bigram][0]

            # Try single words
            for word in word_list:
                if word in self.alias_to_food:
                    return self.alias_to_food[word][0]

        # Step 3: Check if ingredient name contains any alias (longest first)
        best_match = None
        best_len = 0
        for alias, (food, _) in self.alias_to_food.items():
            if len(alias) > best_len and alias in name:
                best_match = food
                best_len = len(alias)
        if best_match:
            return best_match

        # Step 4: Check if any alias contains the ingredient name
        # Only if category hint matches
        detected_cat = self._detect_category(name)
        if detected_cat:
            best_match = None
            best_len = 0
            for alias, (food, food_name) in self.alias_to_food.items():
                food_cat = food.get('category', '')
                if food_cat == detected_cat and name in alias and len(alias) < best_len + 10:
                    if len(alias) > best_len:
                        best_match = food
                        best_len = len(alias)
            if best_match:
                return best_match

        # Step 5: Direct name lookup in food DB
        if clean in self.food_by_name:
            return self.food_by_name[clean]

        # No confident match - return empty instead of forcing wrong match
        return {}

    def _detect_category(self, name: str) -> Optional[str]:
        """Detect food category from ingredient name."""
        name_lower = name.lower()
        for keyword, cat in self.name_category_hints.items():
            if keyword in name_lower:
                return cat
        return None

    def parse_ingredient_text(self, text: str) -> List[Dict]:
        """Parse ingredient text like '200g chicken, 150g rice' into structured list."""
        ingredients = []
        pattern = r'(\d+)\s*(?:grams?|g|kg|kilograms?)?\s*(?:of)?\s*([a-zA-Z\s]+?)(?=(?:\d)|(?:$)|(?:,))'

        matches = re.finditer(pattern, text.lower(), re.IGNORECASE)

        for match in matches:
            quantity_str = match.group(1)
            ingredient_name = match.group(2).strip()
            quantity_g = self._parse_quantity(quantity_str)

            food = self.match_ingredient(ingredient_name)
            if food:
                ingredients.append({
                    'name': food.get('name'),
                    'food_id': food.get('id'),
                    'quantity_g': quantity_g,
                    'category': food.get('category'),
                    'co2_kg': food.get('co2_kg')
                })

        return ingredients

    def _parse_quantity(self, quantity_str: str) -> int:
        try:
            return int(quantity_str)
        except ValueError:
            return 100

    def extract_ingredients_from_text(self, text: str) -> List[str]:
        """Extract recognizable ingredient names from free text."""
        found = []
        seen_names = set()
        covered_spans = []  # (start, end) of already-matched regions
        text_lower = text.lower()

        # Check all aliases (longest first to avoid partial matches)
        sorted_aliases = sorted(self.alias_to_food.keys(), key=len, reverse=True)
        for alias in sorted_aliases:
            idx = text_lower.find(alias)
            while idx >= 0:
                # Check this region isn't already covered by a longer match
                alias_end = idx + len(alias)
                already_covered = any(
                    s <= idx and e >= alias_end for s, e in covered_spans
                )
                if not already_covered:
                    food, food_name = self.alias_to_food[alias]
                    if food_name not in seen_names:
                        found.append({
                            'name': food.get('name'),
                            'food_id': food.get('id')
                        })
                        seen_names.add(food_name)
                    covered_spans.append((idx, alias_end))
                idx = text_lower.find(alias, idx + 1)

        return found

    def get_all_ingredient_names(self) -> List[str]:
        return [food.get('name') for food in self.db.get('foods', [])]
