from typing import Dict, List
import json
from core.co2 import load_aliments_db, get_food_by_id, calculate_meal_co2
from core.shopping import estimate_cost, load_prices_db
import config


class BudgetManager:
    def __init__(self, weekly_budget: float, currency: str = "EUR"):
        self.weekly_budget = weekly_budget
        self.currency = currency
        self.daily_spending = {}
    
    def set_weekly_budget(self, amount: float):
        self.weekly_budget = amount
    
    def add_expense(self, day: str, amount: float):
        if day not in self.daily_spending:
            self.daily_spending[day] = 0.0
        self.daily_spending[day] += amount
    
    def get_total_spent(self) -> float:
        return sum(self.daily_spending.values())
    
    def get_remaining_budget(self) -> float:
        return max(0, self.weekly_budget - self.get_total_spent())
    
    def check_budget_feasibility(self, weekly_plan: Dict) -> Dict:
        total_cost = 0.0
        daily_costs = {}
        
        for day, recipe in weekly_plan.items():
            ingredients = recipe.get('ingredients', [])
            cost_info = estimate_cost(ingredients, currency=self.currency)
            daily_cost = cost_info['total_cost']
            daily_costs[day] = daily_cost
            total_cost += daily_cost
        
        is_feasible = total_cost <= self.weekly_budget
        overage = max(0, total_cost - self.weekly_budget)
        
        return {
            'total_cost': round(total_cost, 2),
            'budget': self.weekly_budget,
            'is_feasible': is_feasible,
            'overage': round(overage, 2),
            'daily_costs': daily_costs,
            'currency': self.currency
        }
    
    def suggest_budget_alternatives(self, over_budget_items: List[Dict], 
                                   target_savings: float) -> List[Dict]:
        suggestions = []
        aliments_db = load_aliments_db()
        
        for item in over_budget_items:
            food_id = item.get('food_id')
            food = get_food_by_id(aliments_db, food_id)
            
            if food:
                category = food.get('category')
                co2 = food.get('co2_kg', 0)
                
                if category in ['meat', 'fish']:
                    cheaper_alternatives = []
                    for alt_food in aliments_db.get('foods', []):
                        if alt_food.get('category') == 'plant_protein':
                            alt_co2 = alt_food.get('co2_kg', 0)
                            if alt_co2 < co2:
                                cheaper_alternatives.append({
                                    'original': food.get('name'),
                                    'alternative': alt_food.get('name'),
                                    'savings_potential': round((co2 - alt_co2) * item.get('quantity_g', 100) / 1000, 2)
                                })
                    
                    if cheaper_alternatives:
                        suggestions.extend(cheaper_alternatives[:2])
        
        return suggestions
    
    def format_budget_summary(self, weekly_plan: Dict) -> Dict:
        feasibility = self.check_budget_feasibility(weekly_plan)
        
        summary = {
            'budget': self.weekly_budget,
            'total_spent': feasibility['total_cost'],
            'remaining': round(self.weekly_budget - feasibility['total_cost'], 2),
            'percentage_used': round((feasibility['total_cost'] / self.weekly_budget) * 100, 1),
            'status': 'under_budget' if feasibility['is_feasible'] else 'over_budget',
            'daily_breakdown': feasibility['daily_costs'],
            'currency': self.currency
        }
        
        return summary
    
    def reset_weekly(self):
        self.daily_spending = {}
